"""Load the brand kit and resolve asset paths relative to the studio root."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

STUDIO_ROOT = Path(__file__).resolve().parent.parent          # marketing/ugc-studio/
BRANDKIT_PATH = STUDIO_ROOT / "brandkit.yaml"

_DEFAULT_BENGALI_REGULAR = "/usr/share/fonts/truetype/noto/NotoSansBengali-Regular.ttf"
_DEFAULT_BENGALI_BOLD = "/usr/share/fonts/truetype/noto/NotoSansBengali-Bold.ttf"
_DEFAULT_LATIN = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def _resolve(p: str) -> str:
    """Resolve a path from the brand kit relative to the studio root."""
    path = Path(os.path.expanduser(p))
    if not path.is_absolute():
        path = (STUDIO_ROOT / path).resolve()
    return str(path)


@dataclass
class BrandKit:
    name: str
    handle: str
    website: str
    spine_bn: str
    spine_en: str
    footer_bn: str
    contact_bn: str
    verify_bn: str
    colors: dict
    fonts: dict
    assets: dict
    disclosure: dict
    raw: dict = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path = BRANDKIT_PATH) -> "BrandKit":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        fonts = data.get("fonts", {})

        # fall back to installed system fonts if a configured font is missing.
        # NB: Path("").exists() is True (it resolves to "."), so test the value first.
        def _fallback(key: str, default: str) -> None:
            val = fonts.get(key)
            if not val or not Path(val).exists():
                fonts[key] = default

        _fallback("bengali_bold", _DEFAULT_BENGALI_BOLD)
        _fallback("bengali_regular", _DEFAULT_BENGALI_REGULAR)
        _fallback("latin", _DEFAULT_LATIN)
        assets = {k: _resolve(v) for k, v in data.get("assets", {}).items()}
        return cls(
            name=data.get("name", "Keystone Education"),
            handle=data.get("handle", ""),
            website=data.get("website", ""),
            spine_bn=data.get("spine_bn", ""),
            spine_en=data.get("spine_en", ""),
            footer_bn=data.get("footer_bn", ""),
            contact_bn=data.get("contact_bn", ""),
            verify_bn=data.get("verify_bn", ""),
            colors=data.get("colors", {}),
            fonts=fonts,
            assets=assets,
            disclosure=data.get("disclosure", {}),
            raw=data,
        )

    def color(self, key: str, default: str = "#000000") -> str:
        return self.colors.get(key, default)

    def asset(self, key: str) -> str | None:
        path = self.assets.get(key)
        return path if path and Path(path).exists() else None
