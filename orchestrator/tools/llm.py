"""LLM access — Groq free tier → Ollama local → mock. Endpoint-allowlisted.

The mock is not a toy: it lets the ENTIRE pipeline run offline, $0, with no
keys, which is the founder's hard constraint. Real generation only improves
phrasing of drafts a human already approves.
"""
from __future__ import annotations

import json
import urllib.request

from ..config import CFG, LLM_ALLOWLIST


class LLMError(RuntimeError):
    pass


def _check_endpoint(url: str) -> None:
    if not any(url.startswith(a) for a in LLM_ALLOWLIST):
        raise LLMError(f"endpoint '{url}' not in open-source/zero-spend allowlist")


def _groq(system: str, user: str, max_tokens: int) -> str:
    base = "https://api.groq.com/openai/v1"
    _check_endpoint(base)
    body = json.dumps({
        "model": CFG.groq_model,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": 0.4, "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(base + "/chat/completions", data=body, method="POST",
                                 headers={"Authorization": f"Bearer {CFG.groq_api_key}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    return data["choices"][0]["message"]["content"].strip()


def _ollama(system: str, user: str) -> str:
    _check_endpoint(CFG.ollama_url)
    body = json.dumps({"model": CFG.ollama_model,
                       "prompt": f"{system}\n\n{user}", "stream": False}).encode()
    req = urllib.request.Request(CFG.ollama_url.rstrip("/") + "/api/generate",
                                 data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode()).get("response", "").strip()


def polish_bn(system: str, user: str, fallback: str, max_tokens: int = 400) -> str:
    """Improve a Bangla draft; on ANY failure return the deterministic template
    fallback. The template already reads well, so the LLM is a nicety, not a
    dependency — the pipeline never breaks for lack of a model."""
    provider = CFG.resolve_llm()
    try:
        if provider == "groq" and CFG.groq_api_key:
            return _groq(system, user, max_tokens)
        if provider == "ollama":
            return _ollama(system, user)
    except Exception:
        return fallback
    return fallback  # mock / default
