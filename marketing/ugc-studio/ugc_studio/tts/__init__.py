"""Bangla TTS providers for the voiceover track.

IMPORTANT (verified 2026-07): Coqui **XTTS-v2 does NOT support Bengali**
(17 languages, no `bn`), and the original coqui-ai/TTS repo is archived. So the
open-source Bangla answer is a different family:

  - sarvam    : Sarvam Bulbul (cloud API) — best Bangla quality, already used by
                the voice-agent; needs SARVAM_API_KEY.
  - indicf5   : AI4Bharat IndicF5 (local, GPU) — near-human, voice-clonable from
                a reference clip; Bengali supported. Runs on the founder's box.
  - parler    : AI4Bharat Indic Parler-TTS (local, GPU) — prompt-controllable
                emotion/pace; Bengali supported.
  - mms       : Meta MMS-TTS bengali (local, CPU-ok, lightweight, robotic).
  - silent    : no voiceover — render captions only, add voice in the editor.

Only `silent` (and `sarvam` with a key) run without a GPU. The local providers
are adapters that shell out to the tool if it's installed; otherwise they raise
a clear "not installed" error with the install pointer.
"""
from __future__ import annotations

from ..config import Config


class TTS:
    name = "base"
    requires_gpu = False

    def available(self) -> bool:
        return False

    def synth(self, text: str, out_wav: str, voice: str = "maya") -> bool:
        raise NotImplementedError


def make_tts(cfg: Config, prefer: str | None = None) -> "TTS":
    choice = prefer or cfg.tts_provider
    if choice == "auto":
        choice = "sarvam" if cfg.sarvam_api_key else "silent"
    providers = {
        "sarvam": lambda: _import("sarvam", "SarvamTTS"),
        "indicf5": lambda: _import("indicf5", "IndicF5TTS"),
        "parler": lambda: _import("parler", "ParlerTTS"),
        "mms": lambda: _import("mms", "MmsTTS"),
        "silent": lambda: _import("silent", "SilentTTS"),
    }
    factory = providers.get(choice, providers["silent"])
    return factory()(cfg)


def _import(mod: str, cls: str):
    import importlib
    m = importlib.import_module(f".{mod}", __name__)
    return getattr(m, cls)
