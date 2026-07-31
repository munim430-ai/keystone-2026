"""AI4Bharat IndicF5 — local Bangla TTS with voice cloning (GPU).

Repo:  https://github.com/AI4Bharat/IndicF5
Model: https://huggingface.co/ai4bharat/IndicF5   (Bengali supported)

IndicF5 clones a voice from a short reference clip + its transcript, then
speaks target text. This is the F5-TTS family already referenced in the
voice-agent's VOICE_CLONING.md — one cloned "Keystone voice" across phone
calls AND video.

This adapter imports the model lazily. If the package/weights aren't installed
it raises with the exact install command instead of a cryptic ImportError.
Runs on the founder's 4GB-VRAM laptop for batch (offline) generation.
"""
from __future__ import annotations

from pathlib import Path

from ..config import Config
from . import TTS

INSTALL_HINT = (
    "IndicF5 not installed. On the GPU box:\n"
    "  git clone https://github.com/AI4Bharat/IndicF5\n"
    "  pip install -r IndicF5/requirements.txt   # or: pip install transformers torch soundfile\n"
    "  # weights auto-download from hf.co/ai4bharat/IndicF5 on first run\n"
    "Then set UGC_INDICF5_REF_WAV / UGC_INDICF5_REF_TXT to a clean Bangla reference clip."
)


class IndicF5TTS(TTS):
    name = "indicf5"
    requires_gpu = True

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.ref_wav = cfg.indicf5_ref_wav
        self.ref_txt = cfg.indicf5_ref_txt
        self._model = None

    def available(self) -> bool:
        try:
            import transformers  # noqa: F401
        except Exception:
            return False
        return bool(self.ref_wav and Path(self.ref_wav).exists())

    def _load(self):
        if self._model is not None:
            return
        try:
            from transformers import AutoModel
        except Exception as e:  # pragma: no cover - env dependent
            raise RuntimeError(INSTALL_HINT) from e
        self._model = AutoModel.from_pretrained(
            "ai4bharat/IndicF5", trust_remote_code=True)

    def synth(self, text: str, out_wav: str, voice: str = "maya",
              seconds: float | None = None) -> bool:  # pragma: no cover - GPU only
        if not (self.ref_wav and Path(self.ref_wav).exists()):
            raise RuntimeError(INSTALL_HINT)
        import soundfile as sf
        self._load()
        audio = self._model(text, ref_audio_path=self.ref_wav, ref_text=self.ref_txt)
        Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
        sf.write(out_wav, audio, samplerate=24000)
        return True
