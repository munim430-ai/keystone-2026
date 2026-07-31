"""Conversation state machine: stages, transitions, prosody, stage guidance."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ..tts import Prosody


class Stage(str, Enum):
    GREETING = "GREETING"
    HOOK = "HOOK"
    QUALIFY = "QUALIFY"
    PITCH = "PITCH"
    OBJECTION = "OBJECTION"
    CLOSE = "CLOSE"
    WRAPUP = "WRAPUP"
    ENDED = "ENDED"


# forward-ish flow; OBJECTION can be entered from anywhere after the hook,
# CLOSE/WRAPUP/ENDED are always reachable (graceful exits must never be blocked)
ALLOWED: dict[Stage, set[Stage]] = {
    Stage.GREETING: {Stage.HOOK, Stage.QUALIFY, Stage.OBJECTION, Stage.CLOSE, Stage.WRAPUP, Stage.ENDED},
    Stage.HOOK: {Stage.QUALIFY, Stage.PITCH, Stage.OBJECTION, Stage.CLOSE, Stage.WRAPUP, Stage.ENDED},
    Stage.QUALIFY: {Stage.PITCH, Stage.OBJECTION, Stage.CLOSE, Stage.WRAPUP, Stage.ENDED},
    Stage.PITCH: {Stage.OBJECTION, Stage.CLOSE, Stage.QUALIFY, Stage.WRAPUP, Stage.ENDED},
    Stage.OBJECTION: {Stage.PITCH, Stage.CLOSE, Stage.OBJECTION, Stage.WRAPUP, Stage.ENDED},
    Stage.CLOSE: {Stage.WRAPUP, Stage.OBJECTION, Stage.ENDED},
    Stage.WRAPUP: {Stage.ENDED},
    Stage.ENDED: set(),
}

# The enthusiasm layer: TTS prosody per stage (values are Sarvam Bulbul ranges)
PROSODY: dict[Stage, Prosody] = {
    Stage.GREETING: Prosody(pace=1.05, pitch=0.15, loudness=1.25),
    Stage.HOOK: Prosody(pace=1.18, pitch=0.25, loudness=1.4),
    Stage.QUALIFY: Prosody(pace=1.0, pitch=0.1, loudness=1.2),
    Stage.PITCH: Prosody(pace=1.0, pitch=0.0, loudness=1.25),
    Stage.OBJECTION: Prosody(pace=0.92, pitch=-0.1, loudness=1.1),
    Stage.CLOSE: Prosody(pace=1.05, pitch=0.15, loudness=1.25),
    Stage.WRAPUP: Prosody(pace=1.0, pitch=0.1, loudness=1.2),
    Stage.ENDED: Prosody(),
}

STAGE_GUIDE: dict[Stage, str] = {
    Stage.GREETING: ("সালাম দিয়ে নিশ্চিত হও ঠিক সেন্টারে কথা বলছ। এক লাইনে নিজের "
                     "পরিচয় দাও, তারপর সাথে সাথে হুকে যাও।"),
    Stage.HOOK: ("দশ সেকেন্ডের হুক: মাসে সম্ভাব্য এক্সট্রা ইনকামের অংকটা বলো এবং "
                 "ত্রিশ সেকেন্ড সময় চাও। এখানে এনার্জি সবচেয়ে বেশি।"),
    Stage.QUALIFY: ("জেনে নাও: ওনাদের স্টুডেন্টরা কি বিদেশে যেতে আগ্রহী? মাসে কতজন "
                    "স্টুডেন্ট? কে সিদ্ধান্ত নেন? একবারে একটাই প্রশ্ন।"),
    Stage.PITCH: ("অফারটা বলো: প্রতি এনরোল হওয়া স্টুডেন্টে পাঁচ হাজার টাকা কমিশন, কোনো "
                  "আপফ্রন্ট ফি নাই, পেমেন্ট এনরোলমেন্টের পরে, ফ্রি সেমিনার, কোরিয়া IELTS "
                  "ছাড়া, মালয়েশিয়া-কানাডা-ইউকে অপশন। সর্বোচ্চ তিন বাক্য, তারপর প্রশ্ন।"),
    Stage.OBJECTION: ("আগে সহানুভূতি ('আমি বুঝি স্যার'), তারপর অবজেকশন ট্রি থেকে জবাব। "
                      "ধীরে, নরম গলায়। দুইবারের বেশি জোরাজুরি নয়।"),
    Stage.CLOSE: ("WhatsApp নাম্বার কনফার্ম করো, বলো অফিসিয়াল নাম্বার থেকে ডিটেইলস "
                  "যাবে, প্রয়োজনে ফলো-আপ কলের সময় ঠিক করো।"),
    Stage.WRAPUP: ("ধন্যবাদ দাও, দোয়া-শুভকামনা, 'আল্লাহ হাফেজ' বলে শেষ করো, তারপর "
                   "end_call টুল কল করো।"),
    Stage.ENDED: "",
}


@dataclass
class ConversationState:
    stage: Stage = Stage.GREETING
    turns: int = 0
    whatsapp: str | None = None
    outcome: str = ""
    outcome_notes: str = ""
    ended: bool = False
    end_reason: str = ""
    transfer_requested: bool = False
    callback_requested: str | None = None  # ISO datetime
    history: list[dict] = field(default_factory=list)

    def advance(self, to: Stage) -> bool:
        if to == self.stage:
            return True
        if to in ALLOWED.get(self.stage, set()):
            self.stage = to
            return True
        return False

    @property
    def prosody(self) -> Prosody:
        return PROSODY[self.stage]

    @property
    def guide(self) -> str:
        return STAGE_GUIDE[self.stage]
