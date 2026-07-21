"""CallSession — the real-time voice loop for one phone call.

Wire in : Twilio Media Streams frames (mu-law 8 kHz, base64) over a WebSocket.
Wire out: mu-law frames back to the same socket.

Pipeline:  frames → VAD (utterance) → STT → SalesAgent(LLM+tools) → TTS → frames

Design notes:
- Barge-in: while the agent is speaking, sustained caller speech clears the
  outbound queue and cancels the current TTS playback.
- A short "filler" clip covers LLM/TTS latency so silence never drags.
- Everything is time-boxed by cfg.max_call_seconds and the kill switch.
"""
from __future__ import annotations

import asyncio
import base64
import time

import numpy as np

from .agent import SalesAgent
from .audio import FRAME_BYTES, frames, ulaw_to_pcm16
from .brain import canned_lines
from .config import Config
from .db import Database
from .llm import LLM
from .notify import Notifier
from .stt import STT
from .telephony import clear_message, mark_message, media_message
from .tts import CachedTTS, Prosody
from .vad import UtteranceDetector


class OutboundSink:
    """Abstracts 'send audio to the caller' so live WS and tests share code."""
    async def send_ulaw(self, ulaw: bytes) -> None: ...
    async def clear(self) -> None: ...
    async def close(self) -> None: ...


class WebSocketSink(OutboundSink):
    def __init__(self, websocket, stream_sid: str):
        self.ws = websocket
        self.stream_sid = stream_sid

    async def send_ulaw(self, ulaw: bytes) -> None:
        await self.ws.send_text(media_message(self.stream_sid, ulaw))

    async def clear(self) -> None:
        await self.ws.send_text(clear_message(self.stream_sid))

    async def mark(self, name: str) -> None:
        await self.ws.send_text(mark_message(self.stream_sid, name))


class CallSession:
    def __init__(self, cfg: Config, db: Database, llm: LLM, stt: STT, tts: CachedTTS,
                 center: dict, call_id: int, sink: OutboundSink,
                 notifier: Notifier | None = None, attempt: int = 1):
        self.cfg = cfg
        self.db = db
        self.stt = stt
        self.tts = tts
        self.sink = sink
        self.center = center
        self.call_id = call_id
        self.notifier = notifier
        self.agent = SalesAgent(cfg, db, llm, center, call_id, attempt)
        self.lines = canned_lines(cfg, center.get("name", ""))

        self.vad = UtteranceDetector(
            silence_ms=cfg.vad_silence_ms,
            min_speech_ms=cfg.vad_min_speech_ms,
            rms_floor=cfg.vad_rms_floor,
            barge_in_ms=cfg.barge_in_ms,
        )
        self._utterances: asyncio.Queue[np.ndarray] = asyncio.Queue()
        self._speaking = False
        self._cancel_speech = asyncio.Event()
        self._started = time.monotonic()
        self._last_activity = time.monotonic()
        self._silence_prompts = 0
        self._done = asyncio.Event()
        self._processing = False

    # ── inbound frames from Twilio ────────────────────────────────────────
    def feed_ulaw(self, payload_b64: str) -> None:
        """Called for every inbound media frame (20 ms)."""
        try:
            pcm = ulaw_to_pcm16(base64.b64decode(payload_b64))
        except Exception:
            return
        utt = self.vad.feed(pcm)
        # barge-in: caller talks over the agent
        if self._speaking and self.vad.barge_in():
            self._cancel_speech.set()
        if utt is not None:
            self._last_activity = time.monotonic()
            self._silence_prompts = 0
            self._utterances.put_nowait(utt)

    # ── outbound speech ───────────────────────────────────────────────────
    async def _speak(self, ulaw: bytes) -> None:
        """Stream mu-law to caller in real time, honoring barge-in."""
        if not ulaw:
            return
        self._speaking = True
        self._cancel_speech.clear()
        try:
            for frame in frames(ulaw, FRAME_BYTES):
                if self._cancel_speech.is_set():
                    await self.sink.clear()
                    break
                await self.sink.send_ulaw(frame)
                await asyncio.sleep(0.02)  # real-time pacing (20 ms/frame)
        finally:
            self._speaking = False

    async def _say_text(self, text: str, prosody: Prosody) -> None:
        if not text:
            return
        ulaw = await self.tts.synth(text, prosody)
        await self._speak(ulaw)

    async def _say_canned(self, key: str, prosody: Prosody | None = None) -> None:
        text = self.lines.get(key, "")
        await self._say_text(text, prosody or self.agent.state.prosody)

    # ── main loop ─────────────────────────────────────────────────────────
    async def run(self) -> None:
        self.db.update_call(self.call_id, status="in_progress")
        # opening line (greeting prosody)
        greeting = self.lines["greeting"]
        self.agent.record_agent_line(greeting)
        from .brain import Stage
        await self._say_text(greeting, self.agent.state.prosody)
        self.agent.state.advance(Stage.HOOK)

        try:
            while not self._done.is_set():
                if self.db.killed:
                    await self._say_canned("kill")
                    self.agent.state.outcome = "killed"
                    self.agent.state.ended = True
                    break
                if time.monotonic() - self._started > self.cfg.max_call_seconds:
                    await self._say_canned("goodbye")
                    self.agent.state.outcome = self.agent.state.outcome or "timeout"
                    self.agent.state.ended = True
                    break
                try:
                    utt = await asyncio.wait_for(self._utterances.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    await self._maybe_prompt_silence()
                    continue
                await self._handle_utterance(utt)
                if self.agent.state.ended:
                    break
        finally:
            await self._finalize()

    async def _handle_utterance(self, utt: np.ndarray) -> None:
        self._processing = True
        t0 = time.monotonic()
        filler_task: asyncio.Task | None = None
        try:
            text = await self.stt.transcribe(utt, sample_rate=8000)
            if not text.strip():
                return
            # cover LLM+TTS latency with a short filler if it runs long
            filler_task = asyncio.create_task(self._delayed_filler())
            reply = await self.agent.respond(text)
            if filler_task:
                filler_task.cancel()
            latency_ms = int((time.monotonic() - t0) * 1000)
            self.db.add_turn(self.call_id, "meta", f"round latency", stage=self.agent.state.stage.value,
                             latency_ms=latency_ms)
            if reply:
                await self._say_text(reply, self.agent.state.prosody)
            self._last_activity = time.monotonic()
        finally:
            if filler_task and not filler_task.done():
                filler_task.cancel()
            self._processing = False

    async def _delayed_filler(self) -> None:
        try:
            await asyncio.sleep(self.cfg.filler_after_ms / 1000)
            key = ["filler_1", "filler_2", "filler_3"][self.agent.state.turns % 3]
            await self._say_canned(key)
        except asyncio.CancelledError:
            pass

    async def _maybe_prompt_silence(self) -> None:
        if self._speaking or self._processing:
            return
        idle = time.monotonic() - self._last_activity
        if idle < 4.0:
            return
        self._silence_prompts += 1
        if self._silence_prompts == 1:
            await self._say_canned("silence_1")
            self._last_activity = time.monotonic()
        elif self._silence_prompts >= 2:
            await self._say_canned("silence_2")
            self.agent.state.ended = True
            self.agent.state.end_reason = "no_response"
            self.db.apply_outcome(self.center["id"], "no_answer")
            self._done.set()

    async def _finalize(self) -> None:
        st = self.agent.state
        outcome = st.outcome or ("completed" if st.ended else "dropped")
        self.db.finish_call(self.call_id, "completed", outcome=outcome,
                            final_stage=st.stage.value,
                            notes=st.outcome_notes)
        if st.whatsapp and self.notifier:
            await self.notifier.send(
                f"🔥 <b>Hot lead</b>\nCenter: {self.center.get('name')}\n"
                f"District: {self.center.get('district')}\nWhatsApp: {st.whatsapp}")
        if st.transfer_requested and self.notifier:
            await self.notifier.send(
                f"📞 <b>Human transfer requested</b>\nCenter: {self.center.get('name')} "
                f"({self.center.get('district')})\nCall back ASAP.")
        self._done.set()

    def stop(self) -> None:
        self._done.set()
        self._cancel_speech.set()
