"""The Script data model: a UGC video is a small, declarative spec.

A Script is what the founder writes (or an LLM drafts). The renderer turns it
into a 9:16 .mp4. It deliberately maps to how a Reel actually works: a hook,
a few beats, a call to action — each beat a caption + a background + a spoken
line.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Which visual engine renders this script.
# - "stills"  : CPU-only, brand images + Ken Burns + captions (works today)
# - "avatar"  : talking-head presenter (SadTalker/Wav2Lip) — needs GPU box
# - "broll"   : generated b-roll (AnimateDiff/LTX) — needs GPU/cloud
VISUALS = ("stills", "avatar", "broll")

PERSONAS = ("student", "father", "mother", "uncle")


@dataclass
class Scene:
    caption_bn: str                 # on-screen Bangla caption (the words that sell)
    voiceover_bn: str = ""          # what the voice says (defaults to caption if empty)
    seconds: float = 2.5
    background: str = "brand_blue"   # brandkit color key, an asset key, or a file path
    emphasis: bool = False          # bigger/gold caption for the hook line

    def spoken(self) -> str:
        return (self.voiceover_bn or self.caption_bn).strip()


@dataclass
class Script:
    id: str
    title: str
    persona: str                    # who this targets (student/father/mother/uncle)
    angle: str                      # the content angle/format
    scenes: list[Scene]
    visuals: str = "stills"
    voice: str = "maya"             # TTS voice preset
    hook_bn: str = ""               # the first 1.5s — the scroll-stopper
    cta_bn: str = ""                # closing call to action
    caption_post_bn: str = ""       # the social caption (feeds Postiz), not on-screen
    hashtags: list[str] = field(default_factory=list)
    ai_presenter: bool = False      # True if a synthetic person/voice presents -> disclosure tag
    needs_consent: bool = False     # True if it would show a real student -> consent gate

    @property
    def total_seconds(self) -> float:
        return round(sum(s.seconds for s in self.scenes), 2)

    def validate_shape(self) -> list[str]:
        errs = []
        if self.persona not in PERSONAS:
            errs.append(f"{self.id}: persona '{self.persona}' not in {PERSONAS}")
        if self.visuals not in VISUALS:
            errs.append(f"{self.id}: visuals '{self.visuals}' not in {VISUALS}")
        if not self.scenes:
            errs.append(f"{self.id}: no scenes")
        return errs


def from_dict(d: dict) -> Script:
    scenes = [Scene(**s) for s in d.get("scenes", [])]
    return Script(
        id=d["id"],
        title=d.get("title", d["id"]),
        persona=d.get("persona", "student"),
        angle=d.get("angle", ""),
        scenes=scenes,
        visuals=d.get("visuals", "stills"),
        voice=d.get("voice", "maya"),
        hook_bn=d.get("hook_bn", ""),
        cta_bn=d.get("cta_bn", ""),
        caption_post_bn=d.get("caption_post_bn", ""),
        hashtags=d.get("hashtags", []),
        ai_presenter=d.get("ai_presenter", False),
        needs_consent=d.get("needs_consent", False),
    )
