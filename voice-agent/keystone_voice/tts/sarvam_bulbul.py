"""Sarvam Bulbul TTS — Bangla with pace/pitch/loudness control."""
from __future__ import annotations

import base64

import httpx
import numpy as np

from . import TTS, Prosody
from ..audio import pcm16_to_ulaw, parse_wav, resample, normalize, TELEPHONY_RATE
from ..bn import split_sentences
from ..config import Config

API_URL = "https://api.sarvam.ai/text-to-speech"


class SarvamTTS(TTS):
    name = "sarvam"

    def __init__(self, cfg: Config):
        self.key = cfg.sarvam_api_key
        self.model = cfg.sarvam_tts_model
        self.speaker = cfg.sarvam_tts_speaker
        self.client = httpx.AsyncClient(timeout=20)

    async def synth(self, text: str, prosody: Prosody) -> bytes:
        p = prosody.clamped()
        pcm_parts: list[np.ndarray] = []
        # Bulbul caps input length per request; sentence-chunk long text
        for chunk in split_sentences(text, max_len=440) or [text]:
            r = await self.client.post(
                API_URL,
                headers={"api-subscription-key": self.key},
                json={
                    "text": chunk,
                    "target_language_code": "bn-IN",
                    "speaker": self.speaker,
                    "model": self.model,
                    "pace": p.pace,
                    "pitch": p.pitch,
                    "loudness": p.loudness,
                    "speech_sample_rate": 8000,
                    "enable_preprocessing": True,
                },
            )
            r.raise_for_status()
            for b64 in r.json().get("audios", []):
                pcm, sr = parse_wav(base64.b64decode(b64))
                pcm_parts.append(resample(pcm, sr, TELEPHONY_RATE))
        if not pcm_parts:
            return b""
        return pcm16_to_ulaw(normalize(np.concatenate(pcm_parts)))

    async def close(self) -> None:
        await self.client.aclose()
