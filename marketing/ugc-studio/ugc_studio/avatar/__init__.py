"""Talking-head avatar adapters (optional, GPU) — verified status 2026-07.

For a synthetic *presenter* (clearly labelled AI, never a fake named student):

  wav2lip  : https://github.com/Rudrabha/Wav2Lip — oldest, lip-only, the ONLY
             one comfortable on ~4GB VRAM. Lower realism. Good enough for a
             brand-mascot presenter over a static Keystone frame.
  sadtalker: https://github.com/OpenTalker/SadTalker — single photo + audio →
             head motion + lip sync. Needs ~6-8GB VRAM to be smooth; borderline
             on 4GB. Best "one still photo → presenter" workflow.
  musetalk : https://github.com/TMElyralab/MuseTalk — 2026 best quality,
             real-time, but needs a driving video and more VRAM. Rent a GPU.

These are shell-out adapters: they call the tool's CLI if the founder has
installed it. The studio never bundles the weights. If the tool isn't present,
`available()` is False and the pipeline falls back to the CPU `stills` renderer
so a video is always produced.

Consent/honesty: the pipeline only lets an avatar drive an `ai_presenter=True`
script, which forces the on-screen AI-disclosure tag (see guardrails).
"""
from __future__ import annotations

import shutil
from pathlib import Path

from ..config import Config


class Avatar:
    name = "base"

    def available(self) -> bool:
        return False

    def render(self, photo: str, audio_wav: str, out_mp4: str) -> bool:
        raise NotImplementedError


class Wav2LipAvatar(Avatar):
    name = "wav2lip"

    def __init__(self, cfg: Config):
        self.repo = cfg.wav2lip_repo
        self.checkpoint = cfg.wav2lip_checkpoint

    def available(self) -> bool:
        return bool(self.repo and Path(self.repo).exists()
                    and self.checkpoint and Path(self.checkpoint).exists())

    def render(self, photo: str, audio_wav: str, out_mp4: str) -> bool:  # pragma: no cover - GPU
        import subprocess
        if not self.available():
            raise RuntimeError(
                "Wav2Lip not configured. git clone https://github.com/Rudrabha/Wav2Lip, "
                "download the checkpoint, then set UGC_WAV2LIP_REPO / UGC_WAV2LIP_CHECKPOINT.")
        cmd = ["python", str(Path(self.repo) / "inference.py"),
               "--checkpoint_path", self.checkpoint,
               "--face", photo, "--audio", audio_wav, "--outfile", out_mp4]
        return subprocess.run(cmd, cwd=self.repo).returncode == 0


class SadTalkerAvatar(Avatar):
    name = "sadtalker"

    def __init__(self, cfg: Config):
        self.repo = cfg.sadtalker_repo

    def available(self) -> bool:
        return bool(self.repo and Path(self.repo).exists())

    def render(self, photo: str, audio_wav: str, out_mp4: str) -> bool:  # pragma: no cover - GPU
        import subprocess
        if not self.available():
            raise RuntimeError(
                "SadTalker not configured. git clone https://github.com/OpenTalker/SadTalker, "
                "run its download_models script, then set UGC_SADTALKER_REPO.")
        out_dir = str(Path(out_mp4).parent)
        cmd = ["python", str(Path(self.repo) / "inference.py"),
               "--source_image", photo, "--driven_audio", audio_wav,
               "--result_dir", out_dir, "--still", "--preprocess", "full"]
        return subprocess.run(cmd, cwd=self.repo).returncode == 0


def make_avatar(cfg: Config) -> Avatar:
    choice = cfg.avatar_provider
    if choice == "wav2lip":
        return Wav2LipAvatar(cfg)
    if choice == "sadtalker":
        return SadTalkerAvatar(cfg)
    return Avatar()  # 'none' → unavailable, pipeline uses stills
