"""Text-to-speech providers. All return raw mu-law @ 8 kHz ready for Twilio.

A content-addressed disk cache sits in front of the provider, so common
phrases (greeting, fillers, goodbyes) cost one API call ever.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from ..config import Config


@dataclass(frozen=True)
class Prosody:
    pace: float = 1.0      # 0.3 – 3.0
    pitch: float = 0.0     # -0.75 – 0.75
    loudness: float = 1.2  # 0.3 – 3.0

    def clamped(self) -> "Prosody":
        return Prosody(
            pace=min(3.0, max(0.3, self.pace)),
            pitch=min(0.75, max(-0.75, self.pitch)),
            loudness=min(3.0, max(0.3, self.loudness)),
        )


class TTS:
    name = "base"

    async def synth(self, text: str, prosody: Prosody) -> bytes:
        """Return mu-law 8 kHz audio for the given Bangla text."""
        raise NotImplementedError

    async def close(self) -> None:
        pass


class CachedTTS(TTS):
    def __init__(self, inner: TTS, cache_dir: str, voice_key: str):
        self.inner = inner
        self.name = inner.name
        self.dir = Path(cache_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.voice_key = voice_key

    def _path(self, text: str, prosody: Prosody) -> Path:
        p = prosody.clamped()
        key = f"{self.voice_key}|{p.pace:.2f}|{p.pitch:.2f}|{p.loudness:.2f}|{text}"
        return self.dir / (hashlib.sha1(key.encode()).hexdigest() + ".ulaw")

    def cached(self, text: str, prosody: Prosody) -> bytes | None:
        path = self._path(text, prosody)
        return path.read_bytes() if path.exists() else None

    async def synth(self, text: str, prosody: Prosody) -> bytes:
        path = self._path(text, prosody)
        if path.exists():
            return path.read_bytes()
        data = await self.inner.synth(text, prosody)
        if data:
            path.write_bytes(data)
        return data

    async def close(self) -> None:
        await self.inner.close()


def make_tts(cfg: Config) -> CachedTTS:
    provider = cfg.tts_provider
    if provider == "auto":
        if cfg.demo_mode or not cfg.sarvam_api_key:
            provider = "mock"
        else:
            provider = "sarvam"
    if provider == "sarvam":
        from .sarvam_bulbul import SarvamTTS
        inner: TTS = SarvamTTS(cfg)
        voice_key = f"{cfg.sarvam_tts_model}:{cfg.sarvam_tts_speaker}"
    else:
        from .mock import MockTTS
        inner = MockTTS()
        voice_key = "mock"
    return CachedTTS(inner, cfg.audio_cache_dir, voice_key)
