"""End-to-end: drive CallSession with synthetic mu-law frames + a fake sink."""
import asyncio

import numpy as np
import pytest

from keystone_voice.audio import FRAME_SAMPLES, pcm16_to_ulaw
from keystone_voice.config import Config
from keystone_voice.db import Database
from keystone_voice.llm.mock import MockLLM
from keystone_voice.session import CallSession, OutboundSink
from keystone_voice.stt.mock import MockSTT
from keystone_voice.tts import make_tts
import base64


class FakeSink(OutboundSink):
    def __init__(self):
        self.bytes_sent = 0
        self.cleared = 0

    async def send_ulaw(self, ulaw: bytes) -> None:
        self.bytes_sent += len(ulaw)

    async def clear(self) -> None:
        self.cleared += 1

    async def close(self) -> None:
        pass


def _speech_frame(level=4000):
    pcm = (np.random.randn(FRAME_SAMPLES) * level).astype(np.int16)
    return base64.b64encode(pcm16_to_ulaw(pcm)).decode()


def _silence_frame():
    return base64.b64encode(pcm16_to_ulaw(np.zeros(FRAME_SAMPLES, dtype=np.int16))).decode()


@pytest.mark.asyncio
async def test_call_session_runs_and_speaks(tmp_path):
    cfg = Config.load()
    cfg.db_path = str(tmp_path / "t.db")
    cfg.demo_mode = True
    cfg.max_call_seconds = 8
    cfg.filler_after_ms = 5000  # don't trigger filler in this short test
    db = Database(cfg.db_path)
    center = {"id": 1, "name": "টেস্ট", "district": "কুমিল্লা", "category": "korean",
              "phone": "+8801711004605", "attempts": 0, "notes": ""}
    db._exec("INSERT INTO centers(id,name,phone) VALUES(1,'টেস্ট','+8801711004605')")
    call_id = db.create_call(1, center["phone"])

    sink = FakeSink()
    session = CallSession(cfg, db, MockLLM(), MockSTT(cfg), make_tts(cfg),
                          center, call_id, sink)

    async def feed_audio():
        # let the greeting play first
        await asyncio.sleep(0.3)
        for _turn in range(3):
            for _ in range(20):      # ~400ms speech
                session.feed_ulaw(_speech_frame())
                await asyncio.sleep(0.002)
            for _ in range(40):      # ~800ms silence -> closes utterance
                session.feed_ulaw(_silence_frame())
                await asyncio.sleep(0.002)
            await asyncio.sleep(0.4)

    feeder = asyncio.create_task(feed_audio())
    try:
        await asyncio.wait_for(session.run(), timeout=12)
    except asyncio.TimeoutError:
        session.stop()
    feeder.cancel()

    assert sink.bytes_sent > 0                       # agent spoke audio
    turns = db.q("SELECT role FROM turns WHERE call_id=?", (call_id,))
    assert any(t["role"] == "agent" for t in turns)  # brain produced replies
    assert any(t["role"] == "caller" for t in turns) # STT captured caller
    call = db.one("SELECT status FROM calls WHERE id=?", (call_id,))
    assert call["status"] == "completed"


@pytest.mark.asyncio
async def test_kill_switch_ends_call(tmp_path):
    cfg = Config.load()
    cfg.db_path = str(tmp_path / "t.db")
    cfg.demo_mode = True
    db = Database(cfg.db_path)
    db._exec("INSERT INTO centers(id,name,phone) VALUES(1,'টেস্ট','+8801711004605')")
    center = db.one("SELECT * FROM centers WHERE id=1")
    call_id = db.create_call(1, center["phone"])
    db.set_killed(True)
    session = CallSession(cfg, db, MockLLM(), MockSTT(cfg), make_tts(cfg),
                          center, call_id, FakeSink())
    await asyncio.wait_for(session.run(), timeout=6)
    call = db.one("SELECT outcome FROM calls WHERE id=?", (call_id,))
    assert call["outcome"] == "killed"
