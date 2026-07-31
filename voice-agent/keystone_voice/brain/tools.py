"""LLM tool schemas + dispatcher: the brain's hands (DB writes, call control)."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from ..db import Database, normalize_bd_phone, utcnow
from .state_machine import ConversationState, Stage

TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "set_stage",
            "description": "কথোপকথনের ধাপ পাল্টাও (GREETING/HOOK/QUALIFY/PITCH/OBJECTION/CLOSE/WRAPUP)",
            "parameters": {
                "type": "object",
                "properties": {"stage": {"type": "string", "enum": [s.value for s in Stage if s != Stage.ENDED]}},
                "required": ["stage"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "capture_whatsapp",
            "description": "সেন্টার মালিকের কনফার্ম করা WhatsApp নাম্বার সেভ করো",
            "parameters": {
                "type": "object",
                "properties": {"number": {"type": "string", "description": "মোবাইল নাম্বার (যেভাবে বলেছে)"}},
                "required": ["number"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_callback",
            "description": "পরে কল করার সময় ঠিক করো",
            "parameters": {
                "type": "object",
                "properties": {
                    "hours_from_now": {"type": "number", "description": "কত ঘণ্টা পরে (আনুমানিক)"},
                    "note": {"type": "string"},
                },
                "required": ["hours_from_now"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mark_outcome",
            "description": "কলের ফলাফল রেকর্ড করো",
            "parameters": {
                "type": "object",
                "properties": {
                    "outcome": {"type": "string",
                                "enum": ["interested", "not_interested", "callback",
                                         "wrong_number", "dnc", "meeting_scheduled"]},
                    "notes": {"type": "string"},
                },
                "required": ["outcome"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_to_human",
            "description": "সিনিয়র (অপারেটর) মানুষের কাছে হ্যান্ডঅফ — জটিল প্রশ্ন বা দর-কষাকষিতে",
            "parameters": {
                "type": "object",
                "properties": {"reason": {"type": "string"}},
                "required": ["reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "end_call",
            "description": "বিদায় বলার পরে কল শেষ করো",
            "parameters": {
                "type": "object",
                "properties": {"reason": {"type": "string"}},
                "required": [],
            },
        },
    },
]


def dispatch(name: str, args: dict, state: ConversationState, db: Database,
             center: dict, call_id: int) -> str:
    """Execute a tool call; returns a short result string fed back to the LLM."""
    if name == "set_stage":
        target = args.get("stage", "")
        try:
            ok = state.advance(Stage(target))
        except ValueError:
            ok = False
        return f"ধাপ এখন: {state.stage.value}" if ok else f"ওই ধাপে যাওয়া যাবে না, এখন: {state.stage.value}"

    if name == "capture_whatsapp":
        raw = str(args.get("number", ""))
        normalized = normalize_bd_phone(raw)
        number = normalized or raw.strip()
        if not number:
            return "নাম্বার বোঝা যায়নি, আবার জিজ্ঞেস করো"
        state.whatsapp = number
        state.outcome = state.outcome or "whatsapp_captured"
        db._exec("UPDATE centers SET whatsapp=?, status='whatsapp_captured' WHERE id=?",
                 (number, center["id"]))
        db.log_event("whatsapp_captured", json.dumps(
            {"center_id": center["id"], "number": number}, ensure_ascii=False))
        return f"WhatsApp সেভ হয়েছে: {number}"

    if name == "schedule_callback":
        try:
            hours = float(args.get("hours_from_now", 24))
        except (TypeError, ValueError):
            hours = 24.0
        hours = min(24 * 14, max(0.5, hours))
        due = (datetime.now(timezone.utc) + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        db.add_callback(center["id"], due, note=str(args.get("note", "")))
        state.callback_requested = due
        state.outcome = state.outcome or "callback"
        return f"কলব্যাক সেট: {round(hours, 1)} ঘণ্টা পরে"

    if name == "mark_outcome":
        outcome = str(args.get("outcome", ""))
        notes = str(args.get("notes", ""))
        state.outcome = outcome
        state.outcome_notes = notes
        db.apply_outcome(center["id"], outcome)
        if notes:
            db._exec("UPDATE centers SET notes=? WHERE id=?",
                     (notes[:500], center["id"]))
        return f"ফলাফল রেকর্ড হয়েছে: {outcome}"

    if name == "transfer_to_human":
        reason = str(args.get("reason", ""))
        state.transfer_requested = True
        due = (datetime.now(timezone.utc) + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        db.add_callback(center["id"], due, note=f"HUMAN TRANSFER: {reason}", priority=9)
        db.log_event("transfer_requested", json.dumps(
            {"center_id": center["id"], "call_id": call_id, "reason": reason}, ensure_ascii=False))
        return "সিনিয়র ম্যানেজারের কলব্যাক সেট হয়েছে — মালিককে জানাও আজই কল আসবে"

    if name == "end_call":
        state.ended = True
        state.end_reason = str(args.get("reason", "completed"))
        return "কল শেষ হচ্ছে"

    return f"অজানা টুল: {name}"
