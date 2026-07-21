"""Mock TTS: audible placeholder tones so the demo pipeline is end-to-end."""
from __future__ import annotations

import numpy as np

from . import TTS, Prosody
from ..audio import pcm16_to_ulaw, TELEPHONY_RATE


class MockTTS(TTS):
    name = "mock"

    async def synth(self, text: str, prosody: Prosody) -> bytes:
        # duration scales with text length; frequency wobbles so it is
        # obviously synthetic but has speech-like rhythm for VAD/latency tests
        seconds = min(6.0, max(0.4, len(text) / 30.0)) / max(0.5, prosody.pace)
        t = np.arange(int(seconds * TELEPHONY_RATE)) / TELEPHONY_RATE
        f0 = 220 * (1 + prosody.pitch)
        wave = 0.35 * np.sin(2 * np.pi * f0 * t + 2.0 * np.sin(2 * np.pi * 3 * t))
        envelope = 0.5 * (1 + np.sin(2 * np.pi * 2.5 * t - np.pi / 2))
        pcm = (wave * envelope * 32767 * min(1.0, prosody.loudness / 2)).astype(np.int16)
        return pcm16_to_ulaw(pcm)
