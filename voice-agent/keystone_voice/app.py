"""FastAPI application: Twilio webhooks, media WebSocket, dashboard REST API."""
from __future__ import annotations

import asyncio
import contextlib
from pathlib import Path

from fastapi import FastAPI, Form, Header, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response

from .config import Config
from .db import Database
from .llm import make_llm
from .notify import Notifier
from .scheduler import Scheduler
from .session import CallSession, WebSocketSink
from .stt import make_stt
from .telephony import Telephony, parse_event
from .tts import make_tts

BASE_DIR = Path(__file__).resolve().parent.parent


class Runtime:
    """Holds shared, long-lived services and active-call bookkeeping."""
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.db = Database(cfg.db_path)
        self.llm = make_llm(cfg)
        self.stt = make_stt(cfg)
        self.tts = make_tts(cfg)
        self.telephony = Telephony(cfg)
        self.notifier = Notifier(cfg)
        self.scheduler = Scheduler(cfg, self.db, self.dial_center)
        # call_row_id -> pending context waiting for the media WS to attach
        self.pending: dict[int, dict] = {}
        self.active: dict[int, CallSession] = {}

    async def dial_center(self, center: dict) -> str:
        """Originate a call to a center and register it as pending."""
        to_number = center["phone"]
        call_id = self.db.create_call(center["id"], to_number)
        self.db.mark_attempt(center["id"])
        attempt = int(center.get("attempts", 0)) + 1
        self.pending[call_id] = {"center": center, "attempt": attempt}
        if self.cfg.demo_mode or not self.telephony.configured:
            # demo: no real PSTN call; the console/sim drives sessions instead
            self.db.update_call(call_id, status="demo_skipped", notes="demo mode: no PSTN dial")
            self.db.log_event("demo_dial", f"center {center['id']} ({center['name']})")
            return f"demo:{call_id}"
        sid = await self.telephony.start_call(to_number, call_id)
        self.db.update_call(call_id, twilio_sid=sid, status="ringing")
        return sid

    async def close(self) -> None:
        await self.scheduler.stop()
        for s in list(self.active.values()):
            s.stop()
        await self.llm.close()
        await self.stt.close()
        await self.tts.close()


def create_app(cfg: Config | None = None) -> FastAPI:
    cfg = cfg or Config.load()
    rt = Runtime(cfg)
    app = FastAPI(title="Keystone Voice Agent")
    app.state.rt = rt

    def check_token(authorization: str | None) -> None:
        if cfg.api_token and authorization != f"Bearer {cfg.api_token}":
            raise HTTPException(status_code=401, detail="unauthorized")

    @app.on_event("startup")
    async def _startup() -> None:
        rt.scheduler.start_auto()

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        await rt.close()

    # ── health / status ───────────────────────────────────────────────────
    @app.get("/health")
    async def health() -> dict:
        return {
            "ok": True,
            "demo_mode": cfg.demo_mode,
            "dialer_mode": cfg.dialer_mode,
            "providers": {"llm": rt.llm.name, "stt": rt.stt.name, "tts": rt.tts.name},
            "twilio_configured": rt.telephony.configured,
            "missing_for_live": cfg.missing_for_live(),
        }

    # ── Twilio webhooks ───────────────────────────────────────────────────
    def _verify_twilio(request: Request, form: dict) -> None:
        if cfg.demo_mode or not rt.telephony.configured:
            return
        sig = request.headers.get("X-Twilio-Signature", "")
        url = str(request.url)
        if not rt.telephony.validate_signature(url, form, sig):
            raise HTTPException(status_code=403, detail="bad Twilio signature")

    @app.post("/twiml/answer")
    async def twiml_answer(request: Request, call_row_id: int) -> Response:
        form = dict(await request.form())
        _verify_twilio(request, form)
        rt.db.update_call(call_row_id, status="answered", answered_at=None)
        return Response(content=rt.telephony.answer_twiml(call_row_id),
                        media_type="application/xml")

    @app.post("/twiml/status")
    async def twiml_status(request: Request, call_row_id: int,
                           CallStatus: str = Form("")) -> PlainTextResponse:
        form = dict(await request.form())
        _verify_twilio(request, form)
        mapping = {"completed": "completed", "busy": "busy", "no-answer": "no_answer",
                   "failed": "failed", "canceled": "canceled"}
        if CallStatus in mapping:
            center = rt.pending.get(call_row_id, {}).get("center")
            if CallStatus in ("busy", "no-answer") and center:
                rt.db.apply_outcome(center["id"], "callback")
                # gentle backoff retry in ~3h
                from datetime import datetime, timedelta, timezone
                due = (datetime.now(timezone.utc) + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
                rt.db.add_callback(center["id"], due, note=f"auto-retry after {CallStatus}")
            row = rt.db.one("SELECT status FROM calls WHERE id=?", (call_row_id,))
            if row and row["status"] not in ("completed",):
                rt.db.update_call(call_row_id, status="completed", outcome=mapping[CallStatus])
        return PlainTextResponse("ok")

    @app.post("/twiml/recording")
    async def twiml_recording(request: Request, call_row_id: int,
                              RecordingUrl: str = Form("")) -> PlainTextResponse:
        form = dict(await request.form())
        _verify_twilio(request, form)
        if RecordingUrl:
            rt.db.update_call(call_row_id, recording_url=RecordingUrl)
        return PlainTextResponse("ok")

    # ── media WebSocket ───────────────────────────────────────────────────
    @app.websocket("/ws/media")
    async def ws_media(ws: WebSocket) -> None:
        await ws.accept()
        session: CallSession | None = None
        run_task: asyncio.Task | None = None
        stream_sid = ""
        try:
            while True:
                raw = await ws.receive_text()
                evt = parse_event(raw)
                kind = evt.get("event")
                if kind == "start":
                    start = evt.get("start", {})
                    stream_sid = evt.get("streamSid", "")
                    params = start.get("customParameters", {})
                    call_row_id = int(params.get("call_row_id", 0))
                    ctx = rt.pending.pop(call_row_id, None)
                    if not ctx:
                        await ws.close()
                        return
                    rt.db.update_call(call_row_id, status="streaming",
                                      answered_at=_now(), twilio_sid=start.get("callSid", ""))
                    sink = WebSocketSink(ws, stream_sid)
                    session = CallSession(cfg, rt.db, rt.llm, rt.stt, rt.tts,
                                          ctx["center"], call_row_id, sink,
                                          rt.notifier, ctx["attempt"])
                    rt.active[call_row_id] = session
                    run_task = asyncio.create_task(session.run())
                elif kind == "media" and session is not None:
                    session.feed_ulaw(evt["media"]["payload"])
                    if session.agent.state.ended and run_task and run_task.done():
                        break
                elif kind == "stop":
                    break
        except WebSocketDisconnect:
            pass
        finally:
            if session is not None:
                session.stop()
                rt.active.pop(session.call_id, None)
            if run_task:
                with contextlib.suppress(Exception):
                    await asyncio.wait_for(run_task, timeout=5)
            with contextlib.suppress(Exception):
                await ws.close()

    # ── dashboard API ─────────────────────────────────────────────────────
    @app.get("/api/stats")
    async def api_stats() -> dict:
        s = rt.db.stats()
        allowed, reason = rt.scheduler.can_call_now()
        s["can_call_now"] = allowed
        s["call_gate_reason"] = reason
        s["active_calls"] = len(rt.active)
        s["providers"] = {"llm": rt.llm.name, "stt": rt.stt.name, "tts": rt.tts.name}
        s["demo_mode"] = cfg.demo_mode
        return s

    @app.get("/api/centers")
    async def api_centers(status: str = "", district: str = "", limit: int = 100) -> list[dict]:
        sql = "SELECT * FROM centers WHERE 1=1"
        args: list = []
        if status:
            sql += " AND status=?"; args.append(status)
        if district:
            sql += " AND district=?"; args.append(district)
        sql += " ORDER BY priority DESC, id ASC LIMIT ?"; args.append(min(500, limit))
        return rt.db.q(sql, tuple(args))

    @app.get("/api/calls")
    async def api_calls(limit: int = 50) -> list[dict]:
        return rt.db.q(
            "SELECT c.*, ce.name AS center_name, ce.district FROM calls c "
            "LEFT JOIN centers ce ON ce.id=c.center_id "
            "ORDER BY c.id DESC LIMIT ?", (min(200, limit),))

    @app.get("/api/calls/{call_id}/transcript")
    async def api_transcript(call_id: int) -> list[dict]:
        return rt.db.q("SELECT role,text,stage,latency_ms,ts FROM turns "
                       "WHERE call_id=? ORDER BY id ASC", (call_id,))

    @app.get("/api/callbacks")
    async def api_callbacks() -> list[dict]:
        return rt.db.q(
            "SELECT k.*, c.name AS center_name, c.district, c.phone FROM callbacks k "
            "JOIN centers c ON c.id=k.center_id WHERE k.done=0 ORDER BY k.priority DESC, k.due_at ASC")

    @app.post("/api/call-next")
    async def api_call_next(authorization: str | None = Header(None)) -> JSONResponse:
        check_token(authorization)
        allowed, reason = rt.scheduler.can_call_now()
        if not allowed:
            return JSONResponse({"ok": False, "reason": reason}, status_code=409)
        center = rt.scheduler.pick_next()
        if center is None:
            return JSONResponse({"ok": False, "reason": "no eligible center"}, status_code=404)
        ref = await rt.dial_center(center)
        return JSONResponse({"ok": True, "center": center["name"], "phone": center["phone"],
                             "ref": ref})

    @app.post("/api/kill")
    async def api_kill(authorization: str | None = Header(None)) -> dict:
        check_token(authorization)
        rt.db.set_killed(True)
        for s in list(rt.active.values()):
            s.stop()
        return {"ok": True, "kill_switch": True}

    @app.post("/api/resume")
    async def api_resume(authorization: str | None = Header(None)) -> dict:
        check_token(authorization)
        rt.db.set_killed(False)
        return {"ok": True, "kill_switch": False}

    @app.get("/api/recording/{call_id}")
    async def api_recording(call_id: int):
        row = rt.db.one("SELECT recording_url FROM calls WHERE id=?", (call_id,))
        if not row or not row["recording_url"]:
            raise HTTPException(status_code=404, detail="no recording")
        audio = await rt.telephony.fetch_recording(row["recording_url"])
        return Response(content=audio, media_type="audio/mpeg")

    # ── dashboard page ────────────────────────────────────────────────────
    @app.get("/", response_class=HTMLResponse)
    async def dashboard() -> HTMLResponse:
        html = (BASE_DIR / "dashboard" / "index.html").read_text(encoding="utf-8")
        return HTMLResponse(html)

    return app


def _now() -> str:
    from .db import utcnow
    return utcnow()
