"""Mock STT for demo mode: plays the part of a coaching-center owner."""
from __future__ import annotations

import numpy as np

from . import STT
from ..config import Config

SCRIPT = [
    "জি বলছি, কে বলছেন?",
    "আচ্ছা, বলেন কী ব্যাপার।",
    "আমাদের তো একটা এজেন্সির সাথে কথা হয়ে আছে।",
    "কমিশনটা কত বললেন?",
    "আচ্ছা ঠিক আছে, WhatsApp এ ডিটেইলস পাঠান। ০১৭১১০০০০০০।",
    "ধন্যবাদ, রাখি তাহলে।",
]


class MockSTT(STT):
    name = "mock"

    def __init__(self, cfg: Config):
        self._i = 0

    async def transcribe(self, pcm: np.ndarray, sample_rate: int = 8000) -> str:
        line = SCRIPT[self._i % len(SCRIPT)]
        self._i += 1
        return line
