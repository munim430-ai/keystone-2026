from datetime import datetime
from zoneinfo import ZoneInfo

from keystone_voice.config import Config
from keystone_voice.db import Database
from keystone_voice.scheduler import Scheduler


def _cfg(tmp_path, **over):
    c = Config.load()
    c.db_path = str(tmp_path / "t.db")
    c.demo_mode = True
    for k, v in over.items():
        setattr(c, k, v)
    return c


async def _noop(center):
    pass


def _sched(cfg):
    return Scheduler(cfg, Database(cfg.db_path), _noop)


def test_business_hours_window(tmp_path):
    cfg = _cfg(tmp_path, call_hours_start=10, call_hours_end=18, timezone="Asia/Dhaka")
    s = _sched(cfg)
    tz = ZoneInfo("Asia/Dhaka")
    assert s.within_business_hours(datetime(2026, 7, 20, 11, 0, tzinfo=tz))   # Monday 11:00
    assert not s.within_business_hours(datetime(2026, 7, 20, 9, 0, tzinfo=tz))
    assert not s.within_business_hours(datetime(2026, 7, 20, 18, 30, tzinfo=tz))


def test_friday_prayer_block(tmp_path):
    cfg = _cfg(tmp_path, timezone="Asia/Dhaka")
    s = _sched(cfg)
    tz = ZoneInfo("Asia/Dhaka")
    # 2026-07-24 is a Friday
    assert not s.within_business_hours(datetime(2026, 7, 24, 13, 0, tzinfo=tz))
    assert s.within_business_hours(datetime(2026, 7, 24, 15, 0, tzinfo=tz))


def test_daily_cap_blocks(tmp_path):
    cfg = _cfg(tmp_path, daily_call_cap=2, call_hours_start=0, call_hours_end=24,
               min_gap_seconds=0)
    s = _sched(cfg)
    for _ in range(2):
        cid = s.db.create_call(0, "+8801700000000")
    allowed, reason = s.can_call_now()
    assert not allowed
    assert "cap" in reason


def test_kill_switch_blocks(tmp_path):
    cfg = _cfg(tmp_path, call_hours_start=0, call_hours_end=24, min_gap_seconds=0)
    s = _sched(cfg)
    s.db.set_killed(True)
    allowed, reason = s.can_call_now()
    assert not allowed
    assert "kill" in reason.lower()
