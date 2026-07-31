"""Sarvam Bulbul cloud TTS for Bangla — best quality, needs SARVAM_API_KEY.

Reuses the same provider Keystone's voice-agent already uses, so the brand
voice is consistent across phone calls and video. Cloud, CPU-side, no GPU.
"""
from __future__ import annotations

import base64
import wave
from pathlib import Path

from ..config import Config
from . import TTS

API_URL = "https://api.sarvam.ai/text-to-speech"

# map studio voice presets -> Sarvam speakers
VOICE_MAP = {"maya": "anushka", "marina": "anushka", "narrator": "abhilash"}


class SarvamTTS(TTS):
    name = "sarvam"
    requires_gpu = False

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.key = cfg.sarvam_api_key
        self.model = cfg.sarvam_tts_model

    def available(self) -> bool:
        return bool(self.key)

    def synth(self, text: str, out_wav: str, voice: str = "maya",
              seconds: float | None = None) -> bool:
        if not self.key:
            raise RuntimeError("SARVAM_API_KEY not set — cannot use sarvam TTS")
        import httpx
        speaker = VOICE_MAP.get(voice, "anushka")
        r = httpx.post(
            API_URL,
            headers={"api-subscription-key": self.key},
            json={"text": text, "target_language_code": "bn-IN", "speaker": speaker,
                  "model": self.model, "speech_sample_rate": 22050,
                  "enable_preprocessing": True},
            timeout=30,
        )
        r.raise_for_status()
        audios = r.json().get("audios", [])
        if not audios:
            return False
        Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
        # Sarvam returns base64 WAV chunks; concatenate PCM
        frames = b""
        params = None
        import io
        for b64 in audios:
            with wave.open(io.BytesIO(base64.b64decode(b64)), "rb") as w:
                params = params or w.getparams()
                frames += w.readframes(w.getnframes())
        with wave.open(out_wav, "wb") as w:
            w.setparams(params)
            w.writeframes(frames)
        return True
