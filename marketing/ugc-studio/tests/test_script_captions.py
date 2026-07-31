import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ugc_studio.captions import strip_emoji, wrap, _runs, font
from ugc_studio.pipeline import load_scripts
from ugc_studio.script import from_dict

STUDIO = Path(__file__).resolve().parent.parent
SCRIPTS = STUDIO / "scripts.yaml"


def test_scripts_yaml_has_20():
    scripts = load_scripts(SCRIPTS)
    assert len(scripts) == 20


def test_every_script_is_about_10s():
    for s in load_scripts(SCRIPTS):
        assert 8.0 <= s.total_seconds <= 12.5, f"{s.id} is {s.total_seconds}s"


def test_every_script_valid_shape():
    for s in load_scripts(SCRIPTS):
        assert s.validate_shape() == []


def test_personas_cover_all_four_buyers():
    personas = {s.persona for s in load_scripts(SCRIPTS)}
    assert {"student", "father", "mother", "uncle"} <= personas


def test_strip_emoji():
    assert strip_emoji("📍 নারসিংদি 📞 বাজার") == "নারসিংদি বাজার"
    assert "🤖" not in strip_emoji("🤖 AI উপস্থাপক")


def test_runs_splits_bengali_and_latin():
    runs = _runs("যাচাই করুন: studyinkorea.go.kr")
    assert any(bn for _, bn in runs)          # has a bengali run
    assert any(not bn for _, bn in runs)      # has a latin run


def test_wrap_respects_width():
    f = font("/usr/share/fonts/truetype/noto/NotoSansBengali-Bold.ttf", 60)
    lines = wrap("কোরিয়ায় পড়াশোনা করতে চান আপনি এখনই শুরু করুন আজকে", f, 600)
    assert len(lines) >= 2


def test_from_dict_roundtrip():
    d = {"id": "x", "persona": "student", "angle": "a",
         "scenes": [{"caption_bn": "ক", "seconds": 2}]}
    s = from_dict(d)
    assert s.id == "x" and len(s.scenes) == 1
