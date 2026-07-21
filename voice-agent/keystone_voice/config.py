"""Central configuration. Everything comes from environment variables / .env."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent  # voice-agent/
load_dotenv(BASE_DIR / ".env")


def _b(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None or not v.strip():
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


def _i(name: str, default: int) -> int:
    v = os.getenv(name, "").strip()
    try:
        return int(v) if v else default
    except ValueError:
        return default


def _s(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip() or default


@dataclass
class Config:
    # master
    demo_mode: bool
    dialer_mode: str            # assist | auto

    # server
    host: str
    port: int
    public_host: str
    api_token: str

    # twilio
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_from_number: str
    record_calls: bool
    amd_enabled: bool

    # llm
    llm_provider: str           # auto | groq | nim | mock
    groq_api_key: str
    llm_model: str
    nim_api_key: str
    nim_base_url: str
    nim_model: str

    # stt
    stt_provider: str           # auto | groq_whisper | sarvam | mock
    sarvam_api_key: str
    sarvam_stt_model: str

    # tts
    tts_provider: str           # auto | sarvam | mock
    sarvam_tts_model: str
    sarvam_tts_speaker: str

    # persona
    persona_name: str
    official_whatsapp: str
    office_location: str
    disclose_ai_upfront: bool

    # calling policy
    timezone: str
    call_hours_start: int
    call_hours_end: int
    daily_call_cap: int
    min_gap_seconds: int
    max_attempts: int
    max_call_seconds: int
    operator_phone: str

    # notifications
    telegram_bot_token: str
    telegram_chat_id: str

    # tuning
    vad_silence_ms: int
    vad_min_speech_ms: int
    vad_rms_floor: int
    barge_in_ms: int
    filler_after_ms: int
    db_path: str
    audio_cache_dir: str

    @classmethod
    def load(cls) -> "Config":
        return cls(
            demo_mode=_b("DEMO_MODE", True),
            dialer_mode=_s("DIALER_MODE", "assist"),
            host=_s("HOST", "127.0.0.1"),
            port=_i("PORT", 8080),
            public_host=_s("PUBLIC_HOST"),
            api_token=_s("API_TOKEN"),
            twilio_account_sid=_s("TWILIO_ACCOUNT_SID"),
            twilio_auth_token=_s("TWILIO_AUTH_TOKEN"),
            twilio_from_number=_s("TWILIO_FROM_NUMBER"),
            record_calls=_b("RECORD_CALLS", True),
            amd_enabled=_b("AMD_ENABLED", False),
            llm_provider=_s("LLM_PROVIDER", "auto"),
            groq_api_key=_s("GROQ_API_KEY"),
            llm_model=_s("LLM_MODEL", "llama-3.3-70b-versatile"),
            nim_api_key=_s("NIM_API_KEY"),
            nim_base_url=_s("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1"),
            nim_model=_s("NIM_MODEL", "meta/llama-3.3-70b-instruct"),
            stt_provider=_s("STT_PROVIDER", "auto"),
            sarvam_api_key=_s("SARVAM_API_KEY"),
            sarvam_stt_model=_s("SARVAM_STT_MODEL", "saarika:v2.5"),
            tts_provider=_s("TTS_PROVIDER", "auto"),
            sarvam_tts_model=_s("SARVAM_TTS_MODEL", "bulbul:v2"),
            sarvam_tts_speaker=_s("SARVAM_TTS_SPEAKER", "anushka"),
            persona_name=_s("PERSONA_NAME", "মায়া"),
            official_whatsapp=_s("OFFICIAL_WHATSAPP", "01328-224600"),
            office_location=_s("OFFICE_LOCATION", "নরসিংদী বাজার"),
            disclose_ai_upfront=_b("DISCLOSE_AI_UPFRONT", False),
            timezone=_s("TIMEZONE", "Asia/Dhaka"),
            call_hours_start=_i("CALL_HOURS_START", 10),
            call_hours_end=_i("CALL_HOURS_END", 18),
            daily_call_cap=_i("DAILY_CALL_CAP", 20),
            min_gap_seconds=_i("MIN_GAP_SECONDS", 180),
            max_attempts=_i("MAX_ATTEMPTS", 3),
            max_call_seconds=_i("MAX_CALL_SECONDS", 420),
            operator_phone=_s("OPERATOR_PHONE"),
            telegram_bot_token=_s("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=_s("TELEGRAM_CHAT_ID"),
            vad_silence_ms=_i("VAD_SILENCE_MS", 600),
            vad_min_speech_ms=_i("VAD_MIN_SPEECH_MS", 240),
            vad_rms_floor=_i("VAD_RMS_FLOOR", 260),
            barge_in_ms=_i("BARGE_IN_MS", 160),
            filler_after_ms=_i("FILLER_AFTER_MS", 900),
            db_path=_s("DB_PATH", str(BASE_DIR / "keystone_voice.db")),
            audio_cache_dir=_s("AUDIO_CACHE_DIR", str(BASE_DIR / "assets" / "audio_cache")),
        )

    def missing_for_live(self) -> list[str]:
        """What still needs to be configured before real calls can go out."""
        missing = []
        if not self.twilio_account_sid:
            missing.append("TWILIO_ACCOUNT_SID")
        if not self.twilio_auth_token:
            missing.append("TWILIO_AUTH_TOKEN")
        if not self.twilio_from_number:
            missing.append("TWILIO_FROM_NUMBER")
        if not self.public_host:
            missing.append("PUBLIC_HOST (ngrok / cloudflared hostname)")
        if not (self.groq_api_key or self.nim_api_key):
            missing.append("GROQ_API_KEY or NIM_API_KEY")
        if not self.sarvam_api_key and self.tts_provider in ("auto", "sarvam"):
            missing.append("SARVAM_API_KEY (TTS)")
        if not (self.groq_api_key or self.sarvam_api_key):
            missing.append("GROQ_API_KEY or SARVAM_API_KEY (STT)")
        return missing
