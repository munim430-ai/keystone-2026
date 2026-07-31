import numpy as np

from keystone_voice.audio import FRAME_SAMPLES
from keystone_voice.vad import UtteranceDetector


def _frame(level):
    return (np.random.randn(FRAME_SAMPLES) * level).astype(np.int16)


def _collect(vad, frame_iter):
    result = None
    for f in frame_iter:
        out = vad.feed(f)
        if out is not None:
            result = out
    return result


def test_detects_utterance_after_silence():
    vad = UtteranceDetector(silence_ms=200, min_speech_ms=100, rms_floor=250)
    speech = (_frame(4000) for _ in range(20))    # 400ms speech
    silence = (_frame(20) for _ in range(15))     # close it out
    got = _collect(vad, speech)
    got = _collect(vad, silence) if got is None else got
    assert got is not None
    assert len(got) > FRAME_SAMPLES  # includes pre-roll + speech


def test_ignores_pure_silence():
    vad = UtteranceDetector(silence_ms=200, min_speech_ms=100, rms_floor=250)
    for _ in range(50):
        assert vad.feed(_frame(10)) is None


def test_barge_in_flag_sets_during_speech():
    vad = UtteranceDetector(silence_ms=600, min_speech_ms=100, rms_floor=250, barge_in_ms=80)
    assert not vad.barge_in()
    for _ in range(10):
        vad.feed(_frame(5000))
    assert vad.barge_in()


def test_short_blip_is_discarded():
    vad = UtteranceDetector(silence_ms=200, min_speech_ms=300, rms_floor=250)
    got = _collect(vad, (_frame(4000) for _ in range(3)))   # ~60ms, below 300ms min
    got2 = _collect(vad, (_frame(10) for _ in range(15)))
    assert got is None and got2 is None
