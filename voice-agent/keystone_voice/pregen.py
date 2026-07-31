"""Pre-generate & cache the common phrases with perfect enthusiasm (Layer 3).

Warms the TTS disk cache so greetings/fillers/goodbyes cost zero API calls
at dial time and always sound identical.
"""
from __future__ import annotations

import asyncio

from .brain import PROSODY, Stage, canned_lines
from .config import Config
from .tts import make_tts

# extra high-value phrases worth caching beyond the canned set
EXTRA = {
    "warm_open": (Stage.HOOK, "ওয়াও স্যার, এটা তো দারুন একটা সুযোগ!"),
    "friendly_laugh": (Stage.OBJECTION, "হাহাহা, স্যার আপনি ঠিকই বলেছেন!"),
    "empathy": (Stage.OBJECTION, "আমি বুঝি স্যার, আপনার চিন্তাটা একদম ঠিক আছে।"),
    "korea_hook": (Stage.PITCH, "কোরিয়াতে কিন্তু IELTS ছাড়াই এডমিশন হয়, "
                                "আমাদের ফাউন্ডার নয় বছর ওখানে ছিলেন।"),
}


async def pregen_all(cfg: Config) -> int:
    tts = make_tts(cfg)
    lines = canned_lines(cfg)
    count = 0
    # canned lines at their natural stage prosody
    stage_for = {
        "greeting": Stage.GREETING, "filler_1": Stage.QUALIFY, "filler_2": Stage.QUALIFY,
        "filler_3": Stage.QUALIFY, "silence_1": Stage.QUALIFY, "silence_2": Stage.WRAPUP,
        "goodbye": Stage.WRAPUP, "kill": Stage.WRAPUP,
    }
    for key, text in lines.items():
        prosody = PROSODY[stage_for.get(key, Stage.PITCH)]
        data = await tts.synth(text, prosody)
        count += 1 if data else 0
        print(f"  cached {key}: {len(data)} bytes")
    for key, (stage, text) in EXTRA.items():
        data = await tts.synth(text, PROSODY[stage])
        count += 1 if data else 0
        print(f"  cached {key}: {len(data)} bytes")
    await tts.close()
    return count


def main(cfg: Config) -> None:
    n = asyncio.run(pregen_all(cfg))
    print(f"\nPre-generated {n} audio clips into {cfg.audio_cache_dir}")
    if cfg.demo_mode or cfg.tts_provider == "mock":
        print("(mock TTS — placeholder tones. Set real SARVAM_API_KEY + DEMO_MODE=0 "
              "to cache real voice.)")
