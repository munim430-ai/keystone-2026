"""Sarvam Saarika STT — Bangla-native, strong on code-switching."""
from __future__ import annotations

import httpx
import numpy as np

from . import STT
from ..audio import resample, wav_bytes
from ..config import Config

API_URL = "https://api.sarvam.ai/speech-to-text"


class SarvamSTT(STT):
    name = "sarvam"

    def __init__(self, cfg: Config):
        self.key = cfg.sarvam_api_key
        self.model = cfg.sarvam_stt_model
        self.client = httpx.AsyncClient(timeout=15)

    async def transcribe(self, pcm: np.ndarray, sample_rate: int = 8000) -> str:
        wav = wav_bytes(resample(pcm, sample_rate, 16000), 16000)
        r = await self.client.post(
            API_URL,
            headers={"api-subscription-key": self.key},
            data={"model": self.model, "language_code": "bn-IN"},
            files={"file": ("utt.wav", wav, "audio/wav")},
        )
        r.raise_for_status()
        return (r.json().get("transcript") or "").strip()

    async def close(self) -> None:
        await self.client.aclose()
