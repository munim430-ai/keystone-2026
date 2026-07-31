"""SalesAgent: one LLM conversation round, including tool execution.

Shared by the live call session and the offline console simulator, so the
brain you test in the terminal is byte-for-byte the brain on the phone.
"""
from __future__ import annotations

import json

from .bn import sanitize_for_tts
from .brain import ConversationState, TOOLS, build_system_prompt, dispatch
from .config import Config
from .db import Database
from .llm import LLM

MAX_TOOL_ROUNDS = 3
MAX_TURNS = 30  # safety: wrap up marathon calls


class SalesAgent:
    def __init__(self, cfg: Config, db: Database, llm: LLM, center: dict,
                 call_id: int, attempt: int = 1):
        self.cfg = cfg
        self.db = db
        self.llm = llm
        self.center = center
        self.call_id = call_id
        self.state = ConversationState()
        self.system_prompt = build_system_prompt(cfg, center, attempt)

    def _messages(self) -> list[dict]:
        stage_msg = {
            "role": "system",
            "content": f"বর্তমান ধাপ: {self.state.stage.value}। গাইড: {self.state.guide}",
        }
        return [{"role": "system", "content": self.system_prompt},
                *self.state.history, stage_msg]

    def record_agent_line(self, text: str, latency_ms: int = 0) -> None:
        self.state.history.append({"role": "assistant", "content": text})
        self.db.add_turn(self.call_id, "agent", text, self.state.stage.value, latency_ms)

    async def respond(self, user_text: str) -> str:
        """Feed one caller utterance, run the LLM (+tools), return the reply."""
        self.state.turns += 1
        self.state.history.append({"role": "user", "content": user_text})
        self.db.add_turn(self.call_id, "caller", user_text, self.state.stage.value)

        if self.state.turns >= MAX_TURNS and not self.state.ended:
            self.state.history.append({
                "role": "system",
                "content": "কল অনেক লম্বা হয়ে গেছে — এখনই ভদ্রভাবে গুটিয়ে আনো এবং end_call করো।",
            })

        reply_text = ""
        for _ in range(MAX_TOOL_ROUNDS):
            reply = await self.llm.chat(self._messages(), tools=TOOLS)
            if reply.content:
                reply_text = reply.content
            if not reply.tool_calls:
                break
            # append the assistant tool-call message, then results
            self.state.history.append({
                "role": "assistant",
                "content": reply.content or None,
                "tool_calls": [
                    {"id": tc.id or f"call_{i}", "type": "function",
                     "function": {"name": tc.name,
                                  "arguments": json.dumps(tc.arguments, ensure_ascii=False)}}
                    for i, tc in enumerate(reply.tool_calls)
                ],
            })
            for i, tc in enumerate(reply.tool_calls):
                result = dispatch(tc.name, tc.arguments, self.state, self.db,
                                  self.center, self.call_id)
                self.state.history.append({
                    "role": "tool",
                    "tool_call_id": tc.id or f"call_{i}",
                    "content": result,
                })
            if self.state.ended:
                break

        reply_text = sanitize_for_tts(reply_text)
        if reply_text:
            self.record_agent_line(reply_text)
        return reply_text
