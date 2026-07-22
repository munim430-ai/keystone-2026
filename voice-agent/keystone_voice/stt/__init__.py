"""Speech-to-text providers. All take 8 kHz int16 PCM, return Bangla text."""
from __future__ import annotations

import numpy as np

from ..config import Config


class STT:
    name = "base"

    async def transcribe(self, pcm: np.ndarray, sample_rate: int = 8000) -> str:
        raise NotImplementedError

    async def close(self) -> None:
        pass


def make_stt(cfg: Config) -> STT:
    provider = cfg.stt_provider
    if provider == "auto":
        if cfg.demo_mode:
            provider = "mock"
        elif cfg.groq_api_key:
            provider = "groq_whisper"
        elif cfg.sarvam_api_key:
            provider = "sarvam"
        else:
            provider = "mock"
    if provider == "groq_whisper":
        from .groq_whisper import GroqWhisperSTT
        return GroqWhisperSTT(cfg)
    if provider == "sarvam":
        from .sarvam import SarvamSTT
        return SarvamSTT(cfg)
    from .mock import MockSTT
    return MockSTT(cfg)
