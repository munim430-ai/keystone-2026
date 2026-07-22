"""NocoDB REST wrapper — the pipeline board + the Drafts approval queue.

Dry-run by default: with no base-url/token it logs the payload it *would*
send (to a local JSONL so the demo has a visible board) and returns. This keeps
the whole system runnable and $0 with zero infrastructure, exactly like the
existing pipeline/nocodb_sync.py --dry-run behaviour.
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from ..config import CFG, ORCH_DIR
from ..models import Draft

# local mirror so `board`/`drafts` CLI works without a live NocoDB
LOCAL_DB = ORCH_DIR / ".local_board"


def _append_local(table: str, row: dict) -> None:
    LOCAL_DB.mkdir(exist_ok=True)
    with open(LOCAL_DB / f"{table}.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _read_local(table: str) -> list[dict]:
    p = LOCAL_DB / f"{table}.jsonl"
    if not p.exists():
        return []
    rows = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            rows[r.get("id") or r.get("student_id") or len(rows)] = r  # last write wins
    return list(rows.values())


def _patch_nocodb(table_id: str, payload: dict) -> tuple[int, str]:
    url = f"{CFG.nocodb_base_url.rstrip('/')}/api/v2/tables/{table_id}/records"
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"xc-token": CFG.nocodb_token,
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status, resp.read().decode()


# -- students board ---------------------------------------------------------
def upsert_student(slug: str, **fields) -> dict:
    row = {"student_id": slug, **fields}
    if CFG.nocodb_live:
        try:
            _patch_nocodb(CFG.nocodb_students_table, row)
        except Exception as e:                       # never let the board break a run
            row["_sync_error"] = str(e)
    _append_local("students", row)
    return row


def board() -> list[dict]:
    return _read_local("students")


# -- drafts approval queue --------------------------------------------------
def enqueue_draft(draft: Draft) -> dict:
    row = draft.to_row()
    if CFG.nocodb_live and CFG.nocodb_drafts_table:
        try:
            _patch_nocodb(CFG.nocodb_drafts_table, row)
        except Exception as e:
            row["_sync_error"] = str(e)
    _append_local("drafts", row)
    return row


def drafts(status: str | None = None) -> list[dict]:
    rows = _read_local("drafts")
    return [r for r in rows if not status or r.get("status") == status]
