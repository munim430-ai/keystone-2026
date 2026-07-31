"""Text console simulator — talk to the brain from the terminal, no telephony.

Runs the *exact* SalesAgent used on real calls, so you can rehearse the
pitch, objection handling, and tool behavior for free (mock or real LLM).
"""
from __future__ import annotations

import asyncio

from .agent import SalesAgent
from .brain import Stage, canned_lines
from .config import Config
from .db import Database
from .llm import make_llm


async def run_console(cfg: Config, center_id: int | None = None) -> None:
    db = Database(cfg.db_path)
    center = (db.one("SELECT * FROM centers WHERE id=?", (center_id,)) if center_id
              else db.one("SELECT * FROM centers WHERE phone LIKE '+8801%' ORDER BY priority DESC"))
    if not center:
        center = {"id": 0, "name": "টেস্ট সেন্টার", "district": "নরসিংদী",
                  "category": "korean", "phone": "+8801700000000", "attempts": 0, "notes": ""}
    llm = make_llm(cfg)
    call_id = db.create_call(center["id"], center["phone"]) if center["id"] else 0
    agent = SalesAgent(cfg, db, llm, center, call_id, attempt=1)
    lines = canned_lines(cfg, center["name"])

    print(f"\n=== কনসোল সিমুলেশন — {center['name']} ({center['district']}, "
          f"{center['category']}) ===")
    print(f"LLM: {llm.name} | ধাপ: {agent.state.stage.value}")
    print("(আপনি সেন্টার মালিক। বাংলায় লিখুন। বেরোতে: 'quit')\n")

    print(f"🤖 {cfg.persona_name}: {lines['greeting']}")
    agent.record_agent_line(lines["greeting"])
    agent.state.advance(Stage.HOOK)

    try:
        while not agent.state.ended:
            try:
                user = input("🧑 মালিক: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if user.lower() in ("quit", "exit", "q"):
                break
            if not user:
                continue
            reply = await agent.respond(user)
            print(f"🤖 {cfg.persona_name} [{agent.state.stage.value}]: {reply}")
            if agent.state.whatsapp:
                print(f"   📱 (WhatsApp captured: {agent.state.whatsapp})")
        print(f"\n=== কল শেষ | outcome={agent.state.outcome or 'n/a'} "
              f"| stage={agent.state.stage.value} ===")
    finally:
        if call_id:
            db.finish_call(call_id, "completed", outcome=agent.state.outcome or "console",
                           final_stage=agent.state.stage.value)
        await llm.close()
