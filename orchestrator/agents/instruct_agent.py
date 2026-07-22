"""InstructAgent — audit verdict → warm Bangla missing-document draft.

Deterministic Jinja2 template first (always correct, always Bangla), optional
LLM polish second. The result is written to the Drafts queue as `pending` —
never sent. Scope is strictly "which document is missing / needs fixing"; the
guardrail refuses anything that strays into visa/bank advice.
"""
from __future__ import annotations

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..config import TEMPLATES_DIR
from .. import guardrails
from ..tools import fs, wa_draft, llm

_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)),
                   autoescape=select_autoescape(enabled_extensions=()),
                   trim_blocks=True, lstrip_blocks=True)

_POLISH_SYSTEM = (
    "তুমি কিস্টোন এডুকেশনের বাংলা কপিরাইটার। নিচের মেসেজটি আরও উষ্ণ ও স্বাভাবিক বাংলায় "
    "লেখো, কিন্তু: (১) কোনো নতুন তথ্য যোগ করবে না, (২) ভিসা বা ব্যাংক ব্যালেন্স নিয়ে কোনো "
    "পরামর্শ বা প্রতিশ্রুতি দেবে না, (৩) 'কোনো ভিসা, কোনো ফি' লাইন ও ফোন নম্বর রাখবে, "
    "(৪) শুধু কোন কাগজ বাকি/ঠিক করতে হবে সেটুকুই বলবে।")


def _humanize(audit_js: dict) -> tuple[list[str], list[str], list[str]]:
    missing, flagged, have = [], [], []
    for d in audit_js.get("documents", []):
        label = d["name"]
        if d["state"] == "MISSING":
            missing.append(label)
        elif d["state"] == "FLAGGED":
            flagged.append(label)
        elif d["state"] == "VERIFIED":
            have.append(label)
    for c in audit_js.get("consistency", []):
        if c["state"] == "MISSING":
            missing.append(f"তথ্যে মিল নেই: {c['rule']}")
        elif c["state"] == "FLAGGED":
            flagged.append(f"যাচাই দরকার: {c['rule']}")
    return missing, flagged, have


def run(slug: str, audit_js: dict | None = None, university: str = "",
        polish: bool = True) -> dict:
    meta = fs.read_meta(slug)
    audit_js = audit_js or fs.latest_audit_json(slug) or {}
    missing, flagged, have = _humanize(audit_js)

    if not university:
        match = fs.read_match(slug)
        university = (match["top"][0]["university"] if match and match.get("top")
                      else "আপনার নির্বাচিত বিশ্ববিদ্যালয়")

    base = _env.get_template("wa_instruction.j2").render(
        name=meta.get("name", ""), university=university,
        missing=missing, flagged=flagged, have=have[:4])

    body = base
    if polish and (missing or flagged):
        body = llm.polish_bn(_POLISH_SYSTEM, base, fallback=base)

    # hard scope + brand guards before anything is queued
    if not guardrails.is_document_checklist_scope(body):
        body = base  # LLM strayed → fall back to the safe template
    guardrails.assert_brand_safe(body)

    d = wa_draft.draft_instruction(
        slug, body, dtype="wa_instruction", subject=f"Missing docs — {university}",
        meta={"missing": len(missing), "flagged": len(flagged)})
    fs.save_instruction(slug, d.id, body)
    return {"draft_id": d.id, "missing": missing, "flagged": flagged,
            "status": d.status, "body_preview": body[:160]}
