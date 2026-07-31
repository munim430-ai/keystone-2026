"""SQLite persistence: centers, calls, transcripts, callbacks, settings.

Synchronous sqlite3 in WAL mode behind a lock — every operation is a
sub-millisecond point read/write, which is fine inside the async server.
"""
from __future__ import annotations

import csv
import json
import re
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS centers(
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  district TEXT DEFAULT '',
  category TEXT DEFAULT 'english',
  phone TEXT DEFAULT '',
  whatsapp TEXT DEFAULT '',
  source_url TEXT DEFAULT '',
  priority INTEGER DEFAULT 1,
  status TEXT DEFAULT 'new',
  attempts INTEGER DEFAULT 0,
  last_called_at TEXT,
  dnc INTEGER DEFAULT 0,
  notes TEXT DEFAULT '',
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_centers_phone ON centers(phone);
CREATE INDEX IF NOT EXISTS idx_centers_status ON centers(status, priority);

CREATE TABLE IF NOT EXISTS calls(
  id INTEGER PRIMARY KEY,
  center_id INTEGER REFERENCES centers(id),
  twilio_sid TEXT DEFAULT '',
  to_number TEXT DEFAULT '',
  started_at TEXT DEFAULT (datetime('now')),
  answered_at TEXT,
  ended_at TEXT,
  duration_sec INTEGER DEFAULT 0,
  status TEXT DEFAULT 'queued',
  outcome TEXT DEFAULT '',
  final_stage TEXT DEFAULT '',
  recording_url TEXT DEFAULT '',
  notes TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_calls_center ON calls(center_id);
CREATE INDEX IF NOT EXISTS idx_calls_started ON calls(started_at);

CREATE TABLE IF NOT EXISTS turns(
  id INTEGER PRIMARY KEY,
  call_id INTEGER REFERENCES calls(id),
  ts TEXT DEFAULT (datetime('now')),
  role TEXT,
  text TEXT,
  stage TEXT DEFAULT '',
  latency_ms INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_turns_call ON turns(call_id);

CREATE TABLE IF NOT EXISTS callbacks(
  id INTEGER PRIMARY KEY,
  center_id INTEGER REFERENCES centers(id),
  due_at TEXT,
  note TEXT DEFAULT '',
  done INTEGER DEFAULT 0,
  priority INTEGER DEFAULT 5,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS events(
  id INTEGER PRIMARY KEY,
  ts TEXT DEFAULT (datetime('now')),
  kind TEXT,
  payload TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
"""

# funnel order used by the dashboard
FUNNEL = ["new", "contacted", "interested", "whatsapp_captured",
          "meeting_scheduled", "contracted", "converted"]
TERMINAL = ["not_interested", "dnc", "wrong_number", "invalid", "exhausted"]

CATEGORY_PRIORITY = {"korean": 4, "ielts": 3, "visa": 3, "japanese": 2, "german": 2, "english": 1}

_CATEGORY_PATTERNS = [
    ("korean", r"korean|korea|kls|topik|কোরিয়"),
    ("japanese", r"japan|jlpt|জাপান"),
    ("german", r"german|goethe|জার্মান"),
    ("visa", r"visa|immigration|consultan|ভিসা"),
    ("ielts", r"ielts|আইইএলটিএস"),
]


def infer_category(name: str) -> str:
    low = name.lower()
    for cat, pat in _CATEGORY_PATTERNS:
        if re.search(pat, low):
            return cat
    return "english"


def normalize_bd_phone(raw: str) -> str | None:
    """Normalize to +8801XXXXXXXXX (13 chars). None if not a BD mobile."""
    digits = re.sub(r"[^\d]", "", raw or "")
    if digits.startswith("880"):
        digits = digits[3:]
    if digits.startswith("0"):
        digits = digits[1:]
    if len(digits) == 10 and digits.startswith("1"):
        return "+880" + digits
    return None


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


class Database:
    def __init__(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._lock = threading.Lock()
        with self._lock:
            self._conn.executescript(SCHEMA)
            self._conn.commit()

    # -- low level ---------------------------------------------------------
    def _exec(self, sql: str, args: tuple = ()) -> sqlite3.Cursor:
        with self._lock:
            cur = self._conn.execute(sql, args)
            self._conn.commit()
            return cur

    def q(self, sql: str, args: tuple = ()) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(sql, args).fetchall()
        return [dict(r) for r in rows]

    def one(self, sql: str, args: tuple = ()) -> dict | None:
        rows = self.q(sql + " LIMIT 1", args)
        return rows[0] if rows else None

    # -- settings / kill switch -------------------------------------------
    def set_setting(self, key: str, value: str) -> None:
        self._exec("INSERT INTO settings(key,value) VALUES(?,?) "
                   "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))

    def get_setting(self, key: str, default: str = "") -> str:
        row = self.one("SELECT value FROM settings WHERE key=?", (key,))
        return row["value"] if row else default

    @property
    def killed(self) -> bool:
        return self.get_setting("kill_switch", "0") == "1"

    def set_killed(self, value: bool) -> None:
        self.set_setting("kill_switch", "1" if value else "0")
        self.log_event("kill_switch", "on" if value else "off")

    # -- centers -----------------------------------------------------------
    def import_centers_csv(self, csv_path: str) -> dict:
        """Import the scraped centers CSV.

        Expected columns (data/IELTS_Partners_Tier2.csv):
        Center Name, Location (District), WhatsApp/Mobile, Source URL
        """
        added = skipped_dup = invalid = 0
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                name = (row.get("Center Name") or row.get("name") or "").strip()
                district = (row.get("Location (District)") or row.get("district") or "").strip()
                raw_phone = (row.get("WhatsApp/Mobile") or row.get("phone") or "").strip()
                url = (row.get("Source URL") or row.get("source_url") or "").strip()
                if not name:
                    continue
                phone = normalize_bd_phone(raw_phone)
                cat = infer_category(name)
                if phone is None:
                    invalid += 1
                    self._exec(
                        "INSERT OR IGNORE INTO centers(name,district,category,phone,source_url,"
                        "priority,status,notes) VALUES(?,?,?,?,?,?,?,?)",
                        (name, district, cat, f"invalid:{raw_phone}:{name[:24]}", url,
                         0, "invalid", f"unparseable number: {raw_phone}"))
                    continue
                cur = self._exec(
                    "INSERT OR IGNORE INTO centers(name,district,category,phone,whatsapp,"
                    "source_url,priority) VALUES(?,?,?,?,?,?,?)",
                    (name, district, cat, phone, phone, url, CATEGORY_PRIORITY.get(cat, 1)))
                if cur.rowcount:
                    added += 1
                else:
                    skipped_dup += 1
        self.log_event("import", json.dumps({"added": added, "dup": skipped_dup, "invalid": invalid}))
        return {"added": added, "duplicates": skipped_dup, "invalid": invalid}

    def next_center(self, max_attempts: int, retry_hours: int = 20) -> dict | None:
        """Pick the next center to dial: due callbacks first, then fresh leads."""
        now = utcnow()
        cb = self.one(
            "SELECT c.*, k.id AS callback_id, k.note AS callback_note FROM callbacks k "
            "JOIN centers c ON c.id=k.center_id "
            "WHERE k.done=0 AND k.due_at<=? AND c.dnc=0 "
            "ORDER BY k.priority DESC, k.due_at ASC", (now,))
        if cb:
            return cb
        retry_before = (datetime.now(timezone.utc) - timedelta(hours=retry_hours)) \
            .strftime("%Y-%m-%d %H:%M:%S")
        return self.one(
            "SELECT * FROM centers WHERE dnc=0 AND status IN ('new','contacted') "
            "AND attempts<? AND phone LIKE '+8801%' "
            "AND (last_called_at IS NULL OR last_called_at<?) "
            "ORDER BY priority DESC, attempts ASC, id ASC",
            (max_attempts, retry_before))

    def apply_outcome(self, center_id: int, outcome: str) -> None:
        """Map a call outcome onto the center's funnel status."""
        status_map = {
            "interested": "interested",
            "whatsapp_captured": "whatsapp_captured",
            "meeting_scheduled": "meeting_scheduled",
            "not_interested": "not_interested",
            "dnc": "not_interested",
            "wrong_number": "wrong_number",
        }
        center = self.one("SELECT * FROM centers WHERE id=?", (center_id,))
        if not center:
            return
        if outcome == "dnc":
            self._exec("UPDATE centers SET dnc=1, status='dnc' WHERE id=?", (center_id,))
            return
        new_status = status_map.get(outcome)
        if new_status is None:
            # attempt-style outcomes (no_answer, busy, callback, ...) keep funnel,
            # but a never-contacted center becomes 'contacted' after an answer
            if outcome in ("callback", "answered") and center["status"] == "new":
                self._exec("UPDATE centers SET status='contacted' WHERE id=?", (center_id,))
            return
        # never regress a center that is further down the funnel
        order = {s: i for i, s in enumerate(FUNNEL)}
        cur_rank = order.get(center["status"], -1)
        new_rank = order.get(new_status, 99)
        if new_status in ("not_interested", "wrong_number") or new_rank > cur_rank:
            self._exec("UPDATE centers SET status=? WHERE id=?", (new_status, center_id))

    def mark_attempt(self, center_id: int) -> None:
        self._exec("UPDATE centers SET attempts=attempts+1, last_called_at=? WHERE id=?",
                   (utcnow(), center_id))
        row = self.one("SELECT attempts, status FROM centers WHERE id=?", (center_id,))
        if row and row["attempts"] >= 3 and row["status"] in ("new", "contacted"):
            self._exec("UPDATE centers SET status='exhausted' WHERE id=? AND status IN ('new','contacted')",
                       (center_id,))

    # -- calls -------------------------------------------------------------
    def create_call(self, center_id: int, to_number: str) -> int:
        # center_id 0/None (console sim, scratch self-test) stored as NULL
        cid = center_id or None
        cur = self._exec("INSERT INTO calls(center_id,to_number,status) VALUES(?,?,'queued')",
                         (cid, to_number))
        return cur.lastrowid

    def update_call(self, call_id: int, **fields) -> None:
        if not fields:
            return
        cols = ", ".join(f"{k}=?" for k in fields)
        self._exec(f"UPDATE calls SET {cols} WHERE id=?", (*fields.values(), call_id))

    def finish_call(self, call_id: int, status: str, outcome: str = "",
                    final_stage: str = "", notes: str = "") -> None:
        row = self.one("SELECT started_at FROM calls WHERE id=?", (call_id,))
        dur = 0
        if row and row["started_at"]:
            try:
                t0 = datetime.strptime(row["started_at"], "%Y-%m-%d %H:%M:%S")
                dur = int((datetime.now(timezone.utc).replace(tzinfo=None) - t0).total_seconds())
            except ValueError:
                pass
        self.update_call(call_id, status=status, outcome=outcome, final_stage=final_stage,
                         ended_at=utcnow(), duration_sec=max(0, dur),
                         notes=notes)

    def add_turn(self, call_id: int, role: str, text: str, stage: str = "",
                 latency_ms: int = 0) -> None:
        self._exec("INSERT INTO turns(call_id,role,text,stage,latency_ms) VALUES(?,?,?,?,?)",
                   (call_id, role, text, stage, latency_ms))

    def calls_today(self, tz_offset_hours: float = 6.0) -> int:
        """Count dials since local midnight (Dhaka is UTC+6, no DST)."""
        local_now = datetime.now(timezone.utc) + timedelta(hours=tz_offset_hours)
        midnight_utc = (local_now.replace(hour=0, minute=0, second=0, microsecond=0)
                        - timedelta(hours=tz_offset_hours)).strftime("%Y-%m-%d %H:%M:%S")
        row = self.one("SELECT COUNT(*) AS n FROM calls WHERE started_at>=?", (midnight_utc,))
        return row["n"] if row else 0

    def last_call_started(self) -> str | None:
        row = self.one("SELECT started_at FROM calls ORDER BY id DESC")
        return row["started_at"] if row else None

    # -- callbacks ---------------------------------------------------------
    def add_callback(self, center_id: int, due_at: str, note: str = "",
                     priority: int = 5) -> int:
        cur = self._exec("INSERT INTO callbacks(center_id,due_at,note,priority) VALUES(?,?,?,?)",
                         (center_id, due_at, note, priority))
        return cur.lastrowid

    def complete_callbacks(self, center_id: int) -> None:
        self._exec("UPDATE callbacks SET done=1 WHERE center_id=? AND done=0", (center_id,))

    # -- events / stats ----------------------------------------------------
    def log_event(self, kind: str, payload: str = "") -> None:
        self._exec("INSERT INTO events(kind,payload) VALUES(?,?)", (kind, payload))

    def stats(self) -> dict:
        funnel = {s: 0 for s in FUNNEL + TERMINAL}
        for row in self.q("SELECT status, COUNT(*) AS n FROM centers GROUP BY status"):
            funnel[row["status"]] = row["n"]
        today = self.calls_today()
        outcomes = {r["outcome"]: r["n"] for r in self.q(
            "SELECT outcome, COUNT(*) AS n FROM calls WHERE outcome!='' GROUP BY outcome")}
        answered = self.one("SELECT COUNT(*) AS n FROM calls WHERE answered_at IS NOT NULL")
        total_calls = self.one("SELECT COUNT(*) AS n FROM calls")
        talk = self.one("SELECT COALESCE(SUM(duration_sec),0) AS s FROM calls")
        return {
            "funnel": funnel,
            "calls_today": today,
            "calls_total": total_calls["n"] if total_calls else 0,
            "answered_total": answered["n"] if answered else 0,
            "talk_seconds": talk["s"] if talk else 0,
            "outcomes": outcomes,
            "kill_switch": self.killed,
        }
