"""Meta MMS-TTS (Bengali) — lightweight local TTS, CPU-capable.

Model: https://huggingface.co/facebook/mms-tts-ben
Repo:  https://github.com/facebookresearch/fairseq/tree/main/examples/mms

Robotic vs IndicF5/Parler, but small and runs on CPU — a usable last resort
for a fully-offline, zero-key voiceover when the GPU providers aren't set up.
"""
from __future__ import annotations

from pathlib import Path

from ..config import Config
from . import TTS

INSTALL_HINT = ("MMS-TTS not installed. pip install transformers torch soundfile "
                "(weights auto-download from hf.co/facebook/mms-tts-ben on first run)")


class MmsTTS(TTS):
    name = "mms"
    requires_gpu = False

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._model = None
        self._tok = None

    def available(self) -> bool:
        try:
            import transformers  # noqa: F401
            return True
        except Exception:
            return False

    def synth(self, text: str, out_wav: str, voice: str = "maya",
              seconds: float | None = None) -> bool:  # pragma: no cover - heavy dep
        try:
            import soundfile as sf
            import torch
            from transformers import VitsModel, AutoTokenizer
        except Exception as e:
            raise RuntimeError(INSTALL_HINT) from e
        if self._model is None:
            self._model = VitsModel.from_pretrained("facebook/mms-tts-ben")
            self._tok = AutoTokenizer.from_pretrained("facebook/mms-tts-ben")
        inputs = self._tok(text, return_tensors="pt")
        with torch.no_grad():
            wav = self._model(**inputs).waveform
        Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
        sf.write(out_wav, wav.squeeze().cpu().numpy(), self._model.config.sampling_rate)
        return True
