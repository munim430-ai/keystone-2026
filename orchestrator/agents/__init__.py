"""Ephemeral sub-agents. Each is a plain function the CEO loop calls per job and
discards on return — no long-lived agent objects, no shared mutable state. A
batch of students = a batch of independent calls.

Every agent's toolset is checked against guardrails.assert_no_send_tools at
import-registration time (see registry below).
"""
from __future__ import annotations

from .. import guardrails

# Declared toolset per agent — asserted to contain NO send/spend tool.
AGENT_TOOLS = {
    "audit": ["fs", "audit_engine"],
    "match": ["fs", "manifests", "master_list"],
    "instruct": ["fs", "llm_polish", "wa_draft"],     # wa_draft writes, never sends
    "scrape": ["fs", "search", "ielts_scraper"],
    "content": ["search", "llm_polish", "draft_queue"],
}

for _agent, _tools in AGENT_TOOLS.items():
    guardrails.assert_no_send_tools(_tools)
