"""Call scheduler: business-hours gating, daily caps, pacing, callbacks.

In `auto` mode a background loop dials centers itself within policy.
In `assist` mode (default, recommended) it never dials on its own — the
operator clicks "Call next" on the dashboard — but the same policy checks
decide whether that button is allowed to fire.
"""
from __future__ import annotations

import asyncio
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .config import Config
from .db import Database


class Scheduler:
    def __init__(self, cfg: Config, db: Database, dialer):
        self.cfg = cfg
        self.db = db
        self.dialer = dialer          # async callable: center -> None
        self.tz = ZoneInfo(cfg.timezone)
        self._task: asyncio.Task | None = None
        self._running = False

    # ── policy ────────────────────────────────────────────────────────────
    def now_local(self) -> datetime:
        return datetime.now(self.tz)

    def within_business_hours(self, when: datetime | None = None) -> bool:
        t = when or self.now_local()
        if t.hour < self.cfg.call_hours_start or t.hour >= self.cfg.call_hours_end:
            return False
        # Friday midday prayer window (Bangladesh): avoid 12:00–14:00
        if t.weekday() == 4 and 12 <= t.hour < 14:
            return False
        return True

    def _tz_offset_hours(self) -> float:
        off = self.now_local().utcoffset()
        return off.total_seconds() / 3600 if off else 0.0

    def gap_ok(self) -> bool:
        last = self.db.last_call_started()
        if not last:
            return True
        try:
            t0 = datetime.strptime(last, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return True
        elapsed = (datetime.utcnow() - t0).total_seconds()
        return elapsed >= self.cfg.min_gap_seconds

    def can_call_now(self) -> tuple[bool, str]:
        """Return (allowed, human-readable reason)."""
        if self.db.killed:
            return False, "kill switch is ON"
        if not self.within_business_hours():
            return False, f"outside business hours ({self.cfg.call_hours_start}:00–{self.cfg.call_hours_end}:00 {self.cfg.timezone})"
        if self.db.calls_today(self._tz_offset_hours()) >= self.cfg.daily_call_cap:
            return False, f"daily cap reached ({self.cfg.daily_call_cap})"
        if not self.gap_ok():
            return False, f"min gap not elapsed ({self.cfg.min_gap_seconds}s between dials)"
        return True, "ok"

    def pick_next(self) -> dict | None:
        return self.db.next_center(self.cfg.max_attempts)

    def seconds_until_open(self) -> int:
        """How long until the next business-hours window opens."""
        t = self.now_local()
        for _ in range(0, 8 * 24):  # scan up to a week ahead, hour by hour
            if self.within_business_hours(t):
                delta = t.replace(minute=0, second=0, microsecond=0) - self.now_local()
                return max(60, int(delta.total_seconds()))
            t += timedelta(hours=1)
        return 3600

    # ── auto loop ─────────────────────────────────────────────────────────
    async def _loop(self) -> None:
        self._running = True
        while self._running:
            allowed, reason = self.can_call_now()
            if not allowed:
                if "outside business hours" in reason:
                    await asyncio.sleep(min(900, self.seconds_until_open()))
                else:
                    await asyncio.sleep(30)
                continue
            center = self.pick_next()
            if center is None:
                await asyncio.sleep(120)  # nothing due right now
                continue
            try:
                await self.dialer(center)
            except Exception as e:  # never let one bad dial kill the loop
                self.db.log_event("dial_error", f"center {center.get('id')}: {e}")
            # pace: min gap + jitter to avoid a robotic cadence
            await asyncio.sleep(self.cfg.min_gap_seconds + random.randint(15, 90))
        # graceful exit

    def start_auto(self) -> None:
        if self.cfg.dialer_mode != "auto":
            return
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
