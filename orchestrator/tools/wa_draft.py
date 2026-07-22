"""The ONLY student-messaging path in the whole system: write a draft.

There is deliberately no send() here. Approval + delivery happen out-of-band
(founder flips status → n8n → Evolution API). This module existing without a
send function is itself the draft-first guardrail.
"""
from __future__ import annotations

from ..models import Draft
from . import db


def draft_instruction(student: str, body_bn: str, dtype: str = "wa_instruction",
                      subject: str = "", meta: dict | None = None) -> Draft:
    d = Draft(student=student, type=dtype, body_bn=body_bn,
              subject=subject, meta=meta or {})
    db.enqueue_draft(d)
    return d


def approve(draft_id: str) -> None:
    """Flip a draft to approved (a human action). Delivery is still someone
    else's job — n8n polls approved drafts and calls Evolution API."""
    import datetime as dt
    from . import db as _db
    _db._append_local("drafts", {
        "id": draft_id, "status": "approved",
        "approved_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")})
