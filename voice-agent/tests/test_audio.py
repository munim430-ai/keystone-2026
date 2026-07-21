import numpy as np

from keystone_voice.audio import (
    pcm16_to_ulaw, ulaw_to_pcm16, resample, wav_bytes, parse_wav, frames,
    FRAME_BYTES, rms, normalize,
)


def test_ulaw_roundtrip_is_close():
    # mu-law is lossy but monotonic; error should be small relative to signal
    t = np.linspace(0, 1, 8000, endpoint=False)
    pcm = (np.sin(2 * np.pi * 440 * t) * 12000).astype(np.int16)
    back = ulaw_to_pcm16(pcm16_to_ulaw(pcm))
    assert back.shape == pcm.shape
    err = np.abs(back.astype(np.int32) - pcm.astype(np.int32))
    assert np.mean(err) < 400  # avg quantization error well under 2% FS


def test_ulaw_encoding_size():
    pcm = np.zeros(160, dtype=np.int16)
    assert len(pcm16_to_ulaw(pcm)) == 160


def test_resample_length():
    pcm = np.arange(16000, dtype=np.int16)
    out = resample(pcm, 16000, 8000)
    assert abs(len(out) - 8000) <= 1


def test_wav_roundtrip():
    pcm = (np.random.randn(1000) * 5000).astype(np.int16)
    data = wav_bytes(pcm, 8000)
    back, sr = parse_wav(data)
    assert sr == 8000
    assert np.array_equal(back, pcm)


def test_frames_are_padded():
    ulaw = b"\x01" * (FRAME_BYTES + 5)
    chunks = list(frames(ulaw))
    assert len(chunks) == 2
    assert all(len(c) == FRAME_BYTES for c in chunks)
    assert chunks[1][-1:] == b"\xff"  # padded with mu-law silence


def test_rms_and_normalize():
    assert rms(np.zeros(100, dtype=np.int16)) == 0.0
    quiet = (np.ones(100) * 100).astype(np.int16)
    loud = normalize(quiet)
    assert np.max(np.abs(loud)) > np.max(np.abs(quiet))
