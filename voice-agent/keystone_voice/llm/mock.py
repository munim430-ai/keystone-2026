"""Scripted mock brain for demo mode and offline tests.

Implements a tiny keyword policy over the same tool interface as the real
LLM, so the whole pipeline (tools, DB writes, state machine) can be
exercised for free.
"""
from __future__ import annotations

import re

from . import LLM, LLMReply, ToolCall

_PHONE_RE = re.compile(r"[০-৯0-9][০-৯0-9\- ]{8,}")


class MockLLM(LLM):
    name = "mock"

    def __init__(self):
        self._turn = 0

    async def chat(self, messages: list[dict], tools: list[dict] | None = None,
                   temperature: float = 0.6, max_tokens: int = 300) -> LLMReply:
        # if the last message is a tool result, just close the loop with text
        last = messages[-1]
        if last.get("role") == "tool":
            return LLMReply(content="জি স্যার, আমাদের অফিসিয়াল নাম্বার থেকে ডিটেইলস চলে যাবে। ধন্যবাদ, আল্লাহ হাফেজ!")

        user_texts = [m["content"] for m in messages if m.get("role") == "user"]
        text = user_texts[-1] if user_texts else ""
        self._turn += 1

        if "কে বলছেন" in text or self._turn == 1:
            return LLMReply(content=(
                "আমি মায়া, কিস্টোন এডুকেশন থেকে বলছি। আপনার সেন্টারের স্টুডেন্টরা বিদেশে "
                "পড়তে গেলে প্রতি স্টুডেন্টে আপনি পাঁচ হাজার টাকা কমিশন পাবেন — ত্রিশ সেকেন্ড সময় হবে?"))
        m = _PHONE_RE.search(text)
        if m and ("whatsapp" in text.lower() or "হোয়াটস" in text or "পাঠান" in text):
            return LLMReply(tool_calls=[
                ToolCall(id="t1", name="capture_whatsapp",
                         arguments={"number": m.group().strip()}),
            ])
        if "এজেন্সি" in text or "এজেন্ট" in text:
            return LLMReply(content=(
                "স্যার, আমরা কম্পিটিশন না — এক্সট্রা অপশন। আপনার আগের এজেন্সিও থাকবে, "
                "আমাদের থেকেও ইনকাম আসবে। কোরিয়াতে IELTS ছাড়াই এডমিশন হয়, এটা কিন্তু বড় সুযোগ।"))
        if "কমিশন" in text or "কত" in text:
            return LLMReply(content=(
                "প্রতি এনরোল হওয়া স্টুডেন্টে পাঁচ হাজার টাকা, কোনো আপফ্রন্ট ফি নাই। "
                "স্টুডেন্ট ভর্তি হওয়ার পরেই পেমেন্ট। আপনার WhatsApp নাম্বারটা কনফার্ম করি?"))
        if "রাখি" in text or "ধন্যবাদ" in text:
            return LLMReply(tool_calls=[
                ToolCall(id="t2", name="end_call", arguments={"reason": "completed"}),
            ], content="অনেক ধন্যবাদ স্যার, ভালো থাকবেন। আল্লাহ হাফেজ!")
        if "না" in text and "লাগবে" in text:
            return LLMReply(tool_calls=[
                ToolCall(id="t3", name="mark_outcome",
                         arguments={"outcome": "not_interested", "notes": "declined"}),
            ], content="কোনো সমস্যা নাই স্যার, সময় দেওয়ার জন্য ধন্যবাদ। আল্লাহ হাফেজ!")
        return LLMReply(content=(
            "আমাদের ফাউন্ডার নয় বছর কোরিয়াতে ছিলেন, অফিস নরসিংদী বাজারে। "
            "আপনার শুধু ইন্টারেস্টেড স্টুডেন্টদের আমাদের নাম্বারটা দিতে হবে — আর কিছুই না।"))
