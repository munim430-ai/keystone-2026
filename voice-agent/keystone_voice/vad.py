"""Energy-based voice activity detection and utterance segmentation.

Works on 20 ms int16 PCM frames at 8 kHz. Coaching centers are noisy, so the
threshold adapts to an EMA noise floor measured during non-speech frames.
"""
from __future__ import annotations

from collections import deque

import numpy as np

from .audio import FRAME_MS, rms


class UtteranceDetector:
    def __init__(
        self,
        silence_ms: int = 600,
        min_speech_ms: int = 240,
        rms_floor: int = 260,
        barge_in_ms: int = 160,
        pre_roll_ms: int = 300,
        max_utterance_ms: int = 15000,
    ):
        self.silence_frames = max(1, silence_ms // FRAME_MS)
        self.min_speech_frames = max(1, min_speech_ms // FRAME_MS)
        self.rms_floor = float(rms_floor)
        self.barge_in_frames = max(1, barge_in_ms // FRAME_MS)
        self.max_frames = max_utterance_ms // FRAME_MS

        self._pre_roll: deque[np.ndarray] = deque(maxlen=max(1, pre_roll_ms // FRAME_MS))
        self._buf: list[np.ndarray] = []
        self._noise = 150.0          # EMA noise floor
        self._in_speech = False
        self._speech_run = 0         # consecutive speech frames (for barge-in)
        self._silence_run = 0
        self._speech_frames = 0

    @property
    def in_speech(self) -> bool:
        return self._in_speech

    def barge_in(self) -> bool:
        """True once the caller has been speaking long enough to interrupt."""
        return self._speech_run >= self.barge_in_frames

    def _is_speech(self, level: float) -> bool:
        return level > max(self.rms_floor, self._noise * 3.0)

    def feed(self, frame: np.ndarray) -> np.ndarray | None:
        """Feed one 20 ms PCM frame. Returns a finished utterance or None."""
        level = rms(frame)
        speech = self._is_speech(level)

        if not speech:
            # only learn the floor from quiet frames
            self._noise = 0.95 * self._noise + 0.05 * level

        if not self._in_speech:
            self._pre_roll.append(frame)
            if speech:
                self._speech_run += 1
                if self._speech_run >= 2:  # 40ms onset debounce
                    self._in_speech = True
                    self._buf = list(self._pre_roll)
                    self._speech_frames = self._speech_run
                    self._silence_run = 0
            else:
                self._speech_run = 0
            return None

        # in speech
        self._buf.append(frame)
        if speech:
            self._speech_run += 1
            self._speech_frames += 1
            self._silence_run = 0
        else:
            self._silence_run += 1

        done = self._silence_run >= self.silence_frames or len(self._buf) >= self.max_frames
        if not done:
            return None

        utterance = np.concatenate(self._buf) if self._buf else None
        long_enough = self._speech_frames >= self.min_speech_frames
        self._reset()
        if utterance is not None and long_enough:
            return utterance
        return None

    def _reset(self) -> None:
        self._in_speech = False
        self._buf = []
        self._pre_roll.clear()
        self._speech_run = 0
        self._silence_run = 0
        self._speech_frames = 0
