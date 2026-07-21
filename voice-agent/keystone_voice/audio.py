"""Audio primitives: G.711 mu-law codec, resampling, WAV in/out, framing.

Implemented with numpy (no `audioop`, which was removed in Python 3.13).
Telephony format everywhere: 8 kHz, mono, mu-law (Twilio Media Streams).
"""
from __future__ import annotations

import io
import wave

import numpy as np

TELEPHONY_RATE = 8000
FRAME_MS = 20
FRAME_SAMPLES = TELEPHONY_RATE * FRAME_MS // 1000   # 160
FRAME_BYTES = FRAME_SAMPLES                          # 1 byte/sample in mu-law

_BIAS = 0x84
_CLIP = 32635


def pcm16_to_ulaw(pcm: np.ndarray) -> bytes:
    """Encode int16 PCM to 8-bit G.711 mu-law."""
    x = pcm.astype(np.int32)
    sign = x < 0
    mag = np.clip(np.abs(x), 0, _CLIP) + _BIAS
    # exponent = index of highest set bit above bit 7 (mag >= 0x84 so log2 >= 7)
    exp = (np.floor(np.log2(mag)).astype(np.int32) - 7).clip(0, 7)
    mantissa = (mag >> (exp + 3)) & 0x0F
    u = (exp << 4) | mantissa
    u = np.where(sign, u | 0x80, u)
    return (~u & 0xFF).astype(np.uint8).tobytes()


def ulaw_to_pcm16(data: bytes) -> np.ndarray:
    """Decode 8-bit G.711 mu-law to int16 PCM."""
    u = ~np.frombuffer(data, dtype=np.uint8) & 0xFF
    sign = (u & 0x80) != 0
    exp = (u >> 4) & 0x07
    mantissa = u & 0x0F
    mag = (((mantissa.astype(np.int32) << 3) + _BIAS) << exp) - _BIAS
    return np.where(sign, -mag, mag).astype(np.int16)


def resample(pcm: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
    """Linear-interpolation resampler; ample for telephony bandwidth."""
    if sr_in == sr_out or len(pcm) == 0:
        return pcm.astype(np.int16)
    n_out = max(1, int(round(len(pcm) * sr_out / sr_in)))
    x_in = np.linspace(0.0, 1.0, num=len(pcm), endpoint=False)
    x_out = np.linspace(0.0, 1.0, num=n_out, endpoint=False)
    return np.interp(x_out, x_in, pcm.astype(np.float64)).astype(np.int16)


def wav_bytes(pcm: np.ndarray, sr: int = TELEPHONY_RATE) -> bytes:
    """int16 mono PCM -> WAV file bytes."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.astype(np.int16).tobytes())
    return buf.getvalue()


def parse_wav(data: bytes) -> tuple[np.ndarray, int]:
    """WAV file bytes -> (int16 mono PCM, sample_rate)."""
    with wave.open(io.BytesIO(data), "rb") as w:
        sr = w.getframerate()
        n_ch = w.getnchannels()
        width = w.getsampwidth()
        raw = w.readframes(w.getnframes())
    if width != 2:
        raise ValueError(f"unsupported sample width: {width}")
    pcm = np.frombuffer(raw, dtype=np.int16)
    if n_ch > 1:
        pcm = pcm.reshape(-1, n_ch).mean(axis=1).astype(np.int16)
    return pcm, sr


def wav_to_ulaw8k(data: bytes) -> bytes:
    pcm, sr = parse_wav(data)
    return pcm16_to_ulaw(resample(pcm, sr, TELEPHONY_RATE))


def frames(ulaw: bytes, size: int = FRAME_BYTES):
    """Yield fixed-size mu-law frames, zero-padding the tail."""
    for i in range(0, len(ulaw), size):
        chunk = ulaw[i:i + size]
        if len(chunk) < size:
            chunk = chunk + b"\xff" * (size - len(chunk))  # 0xff = mu-law silence
        yield chunk


def rms(pcm: np.ndarray) -> float:
    if len(pcm) == 0:
        return 0.0
    return float(np.sqrt(np.mean(pcm.astype(np.float64) ** 2)))


def normalize(pcm: np.ndarray, target_peak: float = 0.85) -> np.ndarray:
    """Peak-normalize with headroom; also acts as a soft noise-gate anchor."""
    peak = float(np.max(np.abs(pcm))) if len(pcm) else 0.0
    if peak < 1:
        return pcm
    gain = min(4.0, target_peak * 32767.0 / peak)
    return np.clip(pcm.astype(np.float64) * gain, -32768, 32767).astype(np.int16)
