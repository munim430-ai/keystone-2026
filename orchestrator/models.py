"""Small dataclasses that flow through the dispatcher."""
from __future__ import annotations

import datetime as dt
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _uid() -> str:
    return uuid.uuid4().hex[:12]


# Draft types the approval queue understands
DRAFT_TYPES = ("wa_instruction", "wa_deadline", "wa_welcome", "fb_post", "b2b_msg")
DRAFT_STATUSES = ("pending", "approved", "sent", "rejected")


@dataclass
class Job:
    """A unit of work the CEO loop hands to an ephemeral sub-agent."""
    kind: str                       # audit | match | instruct | scrape | content
    student: str = ""               # slug, when student-scoped
    payload: dict = field(default_factory=dict)
    id: str = field(default_factory=_uid)
    created: str = field(default_factory=_now)


@dataclass
class Draft:
    """A held, human-approvable message. NOTHING sends without status=approved
    being flipped by a human and a separate n8n/Evolution step acting on it."""
    student: str
    type: str
    body_bn: str
    subject: str = ""
    status: str = "pending"
    id: str = field(default_factory=_uid)
    created: str = field(default_factory=_now)
    approved_at: str = ""
    meta: dict = field(default_factory=dict)

    def to_row(self) -> dict:
        d = asdict(self)
        return d


@dataclass
class Student:
    slug: str
    name: str = ""
    phone: str = ""
    source: str = "whatsapp"
    stage: str = "intake"
    created: str = field(default_factory=_now)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_meta(self) -> dict:
        d = {"name": self.name, "phone": self.phone, "source": self.source,
             "stage": self.stage, "created": self.created}
        d.update(self.extra)
        return d
