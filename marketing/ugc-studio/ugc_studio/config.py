"""Environment-driven config for the UGC studio. All optional; sane defaults."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:
    pass


def _s(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip() or default


@dataclass
class Config:
    # TTS
    tts_provider: str            # auto | sarvam | indicf5 | parler | mms | silent
    sarvam_api_key: str
    sarvam_tts_model: str
    indicf5_ref_wav: str
    indicf5_ref_txt: str
    # avatar
    avatar_provider: str         # none | wav2lip | sadtalker
    wav2lip_repo: str
    wav2lip_checkpoint: str
    sadtalker_repo: str
    # output
    out_dir: str
    fps: int

    @classmethod
    def load(cls) -> "Config":
        studio = Path(__file__).resolve().parent.parent
        return cls(
            tts_provider=_s("UGC_TTS_PROVIDER", "auto"),
            sarvam_api_key=_s("SARVAM_API_KEY"),
            sarvam_tts_model=_s("SARVAM_TTS_MODEL", "bulbul:v2"),
            indicf5_ref_wav=_s("UGC_INDICF5_REF_WAV"),
            indicf5_ref_txt=_s("UGC_INDICF5_REF_TXT"),
            avatar_provider=_s("UGC_AVATAR_PROVIDER", "none"),
            wav2lip_repo=_s("UGC_WAV2LIP_REPO"),
            wav2lip_checkpoint=_s("UGC_WAV2LIP_CHECKPOINT"),
            sadtalker_repo=_s("UGC_SADTALKER_REPO"),
            out_dir=_s("UGC_OUT_DIR", str(studio / "out")),
            fps=int(_s("UGC_FPS", "24")),
        )
