"""LLM brain client — OpenAI-compatible chat completions with tool calling.

One client covers Groq and NVIDIA NIM (both expose the OpenAI schema);
only base_url/model/key differ.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

import httpx

from ..config import Config


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class LLMReply:
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


class LLM:
    name = "base"

    async def chat(self, messages: list[dict], tools: list[dict] | None = None,
                   temperature: float = 0.6, max_tokens: int = 300) -> LLMReply:
        raise NotImplementedError

    async def close(self) -> None:
        pass


class OpenAICompatLLM(LLM):
    def __init__(self, base_url: str, api_key: str, model: str, name: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.name = name
        self.client = httpx.AsyncClient(timeout=20)

    async def chat(self, messages: list[dict], tools: list[dict] | None = None,
                   temperature: float = 0.6, max_tokens: int = 300) -> LLMReply:
        body: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"
        last_err: Exception | None = None
        for _ in range(2):  # one retry on transient failure
            try:
                r = await self.client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=body,
                )
                r.raise_for_status()
                msg = r.json()["choices"][0]["message"]
                calls = []
                for tc in msg.get("tool_calls") or []:
                    try:
                        args = json.loads(tc["function"].get("arguments") or "{}")
                    except json.JSONDecodeError:
                        args = {}
                    calls.append(ToolCall(id=tc.get("id", ""), name=tc["function"]["name"],
                                          arguments=args))
                return LLMReply(content=(msg.get("content") or "").strip(), tool_calls=calls)
            except (httpx.HTTPError, KeyError, IndexError) as e:
                last_err = e
        raise RuntimeError(f"LLM request failed: {last_err}")

    async def close(self) -> None:
        await self.client.aclose()


def make_llm(cfg: Config) -> LLM:
    provider = cfg.llm_provider
    if provider == "auto":
        if cfg.demo_mode:
            provider = "mock"
        elif cfg.groq_api_key:
            provider = "groq"
        elif cfg.nim_api_key:
            provider = "nim"
        else:
            provider = "mock"
    if provider == "groq":
        return OpenAICompatLLM("https://api.groq.com/openai/v1", cfg.groq_api_key,
                               cfg.llm_model, "groq")
    if provider == "nim":
        return OpenAICompatLLM(cfg.nim_base_url, cfg.nim_api_key, cfg.nim_model, "nim")
    from .mock import MockLLM
    return MockLLM()
