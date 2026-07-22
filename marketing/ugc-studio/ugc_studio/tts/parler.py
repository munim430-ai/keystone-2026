"""AI4Bharat Indic Parler-TTS — local Bangla TTS with prompt-controlled style.

Model: https://huggingface.co/ai4bharat/indic-parler-tts   (Bengali supported)
Repo:  https://github.com/huggingface/parler-tts

Unlike a fixed voice, Parler takes a natural-language *description* of the voice
("a young woman, warm and energetic, clear, close mic") alongside the text, so
you can dial enthusiasm per script without a reference clip. GPU, batch/offline.
"""
from __future__ import annotations

from pathlib import Path

from ..config import Config
from . import TTS

INSTALL_HINT = (
    "Indic Parler-TTS not installed. On the GPU box:\n"
    "  pip install git+https://github.com/huggingface/parler-tts.git\n"
    "  # weights auto-download from hf.co/ai4bharat/indic-parler-tts on first run"
)

# per-preset voice description prompts (the 'enthusiasm layer')
DESCRIPTIONS = {
    "maya": "A young Bangladeshi woman, warm, confident and energetic, speaking clear "
            "Bengali at a lively pace, very close and clear recording, no background noise.",
    "narrator": "A calm, trustworthy Bengali narrator, measured pace, warm tone, "
                "studio-clear recording.",
}


class ParlerTTS(TTS):
    name = "parler"
    requires_gpu = True

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._model = None
        self._tok = None
        self._desc_tok = None

    def available(self) -> bool:
        try:
            import parler_tts  # noqa: F401
            return True
        except Exception:
            return False

    def synth(self, text: str, out_wav: str, voice: str = "maya",
              seconds: float | None = None) -> bool:  # pragma: no cover - GPU only
        try:
            import soundfile as sf
            import torch
            from parler_tts import ParlerTTSForConditionalGeneration
            from transformers import AutoTokenizer
        except Exception as e:
            raise RuntimeError(INSTALL_HINT) from e
        if self._model is None:
            name = "ai4bharat/indic-parler-tts"
            self._model = ParlerTTSForConditionalGeneration.from_pretrained(name)
            self._tok = AutoTokenizer.from_pretrained(name)
            self._desc_tok = AutoTokenizer.from_pretrained(self._model.config.text_encoder._name_or_path)
        desc = DESCRIPTIONS.get(voice, DESCRIPTIONS["maya"])
        d = self._desc_tok(desc, return_tensors="pt")
        p = self._tok(text, return_tensors="pt")
        out = self._model.generate(input_ids=d.input_ids, attention_mask=d.attention_mask,
                                   prompt_input_ids=p.input_ids, prompt_attention_mask=p.attention_mask)
        Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
        sf.write(out_wav, out.cpu().numpy().squeeze(), self._model.config.sampling_rate)
        return True
