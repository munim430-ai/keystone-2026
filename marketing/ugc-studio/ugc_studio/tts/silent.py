"""Silent voiceover track: sized to the script so captions have room to breathe.

Produces a valid silent WAV of the requested duration so the render still muxes
audio cleanly. Founder records/adds the real voiceover in the editor, or swaps
in a real TTS provider.
"""
from __future__ import annotations

import struct
import wave
from pathlib import Path

from ..config import Config
from . import TTS


class SilentTTS(TTS):
    name = "silent"
    requires_gpu = False

    def __init__(self, cfg: Config):
        self.cfg = cfg

    def available(self) -> bool:
        return True

    def synth(self, text: str, out_wav: str, voice: str = "maya",
              seconds: float | None = None) -> bool:
        # ~0.18s per Bangla word is a natural narration pace
        dur = seconds if seconds else max(1.0, len(text.split()) * 0.18)
        sr = 16000
        n = int(dur * sr)
        Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
        with wave.open(out_wav, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes(struct.pack("<%dh" % n, *([0] * n)))
        return True
