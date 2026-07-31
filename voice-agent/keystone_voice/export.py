"""Export centers / call outcomes to CSV for operator review."""
from __future__ import annotations

import csv
import sys

from .db import Database


def export_centers(db: Database, out_path: str | None) -> int:
    rows = db.q("SELECT id,name,district,category,phone,whatsapp,status,attempts,"
                "last_called_at,notes FROM centers ORDER BY status, district, name")
    cols = ["id", "name", "district", "category", "phone", "whatsapp", "status",
            "attempts", "last_called_at", "notes"]
    _write(rows, cols, out_path)
    return len(rows)


def export_calls(db: Database, out_path: str | None) -> int:
    rows = db.q(
        "SELECT c.id,ce.name AS center,ce.district,c.to_number,c.started_at,"
        "c.duration_sec,c.status,c.outcome,c.final_stage,c.recording_url "
        "FROM calls c LEFT JOIN centers ce ON ce.id=c.center_id ORDER BY c.id")
    cols = ["id", "center", "district", "to_number", "started_at", "duration_sec",
            "status", "outcome", "final_stage", "recording_url"]
    _write(rows, cols, out_path)
    return len(rows)


def _write(rows: list[dict], cols: list[str], out_path: str | None) -> None:
    f = open(out_path, "w", newline="", encoding="utf-8-sig") if out_path else sys.stdout
    try:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    finally:
        if out_path:
            f.close()
