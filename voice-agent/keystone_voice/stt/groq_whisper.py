"""Groq-hosted Whisper large-v3 — fast, cheap, solid Bangla accuracy."""
from __future__ import annotations

import httpx
import numpy as np

from . import STT
from ..audio import resample, wav_bytes
from ..config import Config

API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"


class GroqWhisperSTT(STT):
    name = "groq_whisper"

    def __init__(self, cfg: Config):
        self.key = cfg.groq_api_key
        self.client = httpx.AsyncClient(timeout=15)

    async def transcribe(self, pcm: np.ndarray, sample_rate: int = 8000) -> str:
        # upsample to 16 kHz — whisper's native rate, slightly better accuracy
        wav = wav_bytes(resample(pcm, sample_rate, 16000), 16000)
        r = await self.client.post(
            API_URL,
            headers={"Authorization": f"Bearer {self.key}"},
            data={"model": "whisper-large-v3", "language": "bn",
                  "temperature": "0", "response_format": "json"},
            files={"file": ("utt.wav", wav, "audio/wav")},
        )
        r.raise_for_status()
        return (r.json().get("text") or "").strip()

    async def close(self) -> None:
        await self.client.aclose()
