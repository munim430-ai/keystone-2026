"""Twilio integration: originate calls, TwiML, Media Streams protocol helpers.

Design decisions (see OPERATIONS.md):
- ONE consistent caller ID. No rotation — rotation is a robocaller pattern,
  violates Twilio's Acceptable Use Policy, and kills callback trust.
- Every call optionally recorded; recordings proxied through our server so
  Twilio credentials never reach the browser.
"""
from __future__ import annotations

import asyncio
import base64
import json
from typing import Any
from xml.sax.saxutils import quoteattr

import httpx
from twilio.request_validator import RequestValidator
from twilio.rest import Client

from .config import Config


class Telephony:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._client: Client | None = None
        self._validator: RequestValidator | None = None
        if cfg.twilio_account_sid and cfg.twilio_auth_token:
            self._client = Client(cfg.twilio_account_sid, cfg.twilio_auth_token)
            self._validator = RequestValidator(cfg.twilio_auth_token)

    @property
    def configured(self) -> bool:
        return self._client is not None and bool(self.cfg.twilio_from_number)

    def validate_signature(self, url: str, params: dict, signature: str) -> bool:
        if self._validator is None:
            return True
        return self._validator.validate(url, params, signature)

    async def start_call(self, to_number: str, call_row_id: int) -> str:
        """Originate an outbound call; returns the Twilio Call SID."""
        if not self.configured:
            raise RuntimeError("Twilio is not configured (see .env)")
        base = f"https://{self.cfg.public_host}"
        kwargs: dict[str, Any] = dict(
            to=to_number,
            from_=self.cfg.twilio_from_number,
            url=f"{base}/twiml/answer?call_row_id={call_row_id}",
            method="POST",
            status_callback=f"{base}/twiml/status?call_row_id={call_row_id}",
            status_callback_method="POST",
            status_callback_event=["initiated", "ringing", "answered", "completed"],
            timeout=25,
        )
        if self.cfg.record_calls:
            kwargs["record"] = True
            kwargs["recording_status_callback"] = f"{base}/twiml/recording?call_row_id={call_row_id}"
        if self.cfg.amd_enabled:
            kwargs["machine_detection"] = "Enable"
        call = await asyncio.to_thread(self._client.calls.create, **kwargs)
        return call.sid

    async def hangup(self, call_sid: str) -> None:
        if self._client is None or not call_sid:
            return
        try:
            await asyncio.to_thread(self._client.calls(call_sid).update, status="completed")
        except Exception:
            pass  # already hung up

    def answer_twiml(self, call_row_id: int) -> str:
        """TwiML that bridges the call into our bidirectional media stream."""
        ws = f"wss://{self.cfg.public_host}/ws/media"
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Response><Connect>"
            f"<Stream url={quoteattr(ws)}>"
            f'<Parameter name="call_row_id" value="{int(call_row_id)}"/>'
            "</Stream></Connect></Response>"
        )

    async def fetch_recording(self, recording_url: str) -> bytes:
        """Download a call recording using our credentials (server-side only)."""
        auth = (self.cfg.twilio_account_sid, self.cfg.twilio_auth_token)
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(recording_url + ".mp3", auth=auth)
            r.raise_for_status()
            return r.content


# ── Media Streams wire protocol ──────────────────────────────────────────

def media_message(stream_sid: str, ulaw: bytes) -> str:
    return json.dumps({
        "event": "media",
        "streamSid": stream_sid,
        "media": {"payload": base64.b64encode(ulaw).decode()},
    })


def mark_message(stream_sid: str, name: str) -> str:
    return json.dumps({"event": "mark", "streamSid": stream_sid, "mark": {"name": name}})


def clear_message(stream_sid: str) -> str:
    return json.dumps({"event": "clear", "streamSid": stream_sid})


def parse_event(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"event": "invalid"}
