"""Orchestration: Script → guardrails → voiceover → visuals → .mp4 + caption sidecar.

The visual engine is chosen by the script:
  - stills : CPU renderer (always works)
  - avatar : talking-head if that provider is available, else fall back to stills
  - broll  : documented (AnimateDiff/LTX) — falls back to stills locally

Every render also writes a `<id>.caption.txt` — the ready-to-post Bangla caption
+ hashtags — that the existing marketing/n8n `content-repurpose` flow can hand to
Postiz. So the studio produces the asset AND the post copy together.
"""
from __future__ import annotations

import json
from pathlib import Path

from .avatar import make_avatar
from .brandkit import BrandKit
from .config import Config
from .guardrails import check
from .render import render as render_stills
from .script import Script
from .tts import make_tts


class RenderResult:
    def __init__(self, script_id, ok, video=None, caption=None, meta=None,
                 errors=None, warnings=None, engine="stills"):
        self.script_id = script_id
        self.ok = ok
        self.video = video
        self.caption = caption
        self.meta = meta or {}
        self.errors = errors or []
        self.warnings = warnings or []
        self.engine = engine


def _write_caption(script: Script, brand: BrandKit, path: Path) -> None:
    tags = " ".join(script.hashtags) if script.hashtags else \
        "#StudyInKorea #Bangladesh #Keystone #কোরিয়া #IELTS"
    body = script.caption_post_bn or script.hook_bn or script.title
    footer = f"{brand.footer_bn}\n{brand.contact_bn}\n{brand.verify_bn}"
    path.write_text(f"{body}\n\n{footer}\n\n{tags}\n", encoding="utf-8")


def render_script(script: Script, brand: BrandKit, cfg: Config,
                  strict: bool = True) -> RenderResult:
    errors, warnings = check(script, brand)
    if errors and strict:
        return RenderResult(script.id, ok=False, errors=errors, warnings=warnings)

    out_dir = Path(cfg.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    video_path = out_dir / f"{script.id}.mp4"
    caption_path = out_dir / f"{script.id}.caption.txt"
    audio_path = out_dir / f"{script.id}.voice.wav"

    # 1) voiceover (full-script narration)
    tts = make_tts(cfg)
    narration = " ".join(s.spoken() for s in script.scenes)
    audio_arg = None
    try:
        # SilentTTS/Sarvam accept an optional seconds kwarg; others ignore it
        tts.synth(narration, str(audio_path), voice=script.voice,
                  seconds=script.total_seconds)  # type: ignore[call-arg]
        audio_arg = str(audio_path)
    except TypeError:
        tts.synth(narration, str(audio_path), voice=script.voice)
        audio_arg = str(audio_path)
    except Exception as e:
        warnings.append(f"TTS unavailable ({e}); rendering silent.")
        audio_arg = None

    # 2) visuals
    engine = "stills"
    if script.visuals == "avatar":
        avatar = make_avatar(cfg)
        photo = brand.asset("founder_photo") or brand.asset("marina_photo")
        if avatar.available() and photo and audio_arg:
            try:
                if avatar.render(photo, audio_arg, str(video_path)):
                    engine = avatar.name
                    _write_caption(script, brand, caption_path)
                    return RenderResult(script.id, True, str(video_path),
                                        str(caption_path), {"engine": engine},
                                        warnings=warnings, engine=engine)
            except Exception as e:
                warnings.append(f"avatar '{avatar.name}' failed ({e}); falling back to stills.")
        else:
            warnings.append("avatar engine unavailable; rendering stills (add SadTalker/Wav2Lip on GPU box).")

    if script.visuals == "broll":
        warnings.append("b-roll (AnimateDiff/LTX) is GPU/cloud-only; rendering stills locally. "
                        "See TOOLS.md for the b-roll workflow.")

    # 3) CPU stills render (always works)
    meta = render_stills(script, brand, str(video_path), audio_path=audio_arg, fps=cfg.fps)
    _write_caption(script, brand, caption_path)
    return RenderResult(script.id, True, str(video_path), str(caption_path),
                        meta, warnings=warnings, engine=engine)


def load_scripts(path: str | Path) -> list[Script]:
    import yaml
    from .script import from_dict
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return [from_dict(d) for d in data.get("scripts", [])]
