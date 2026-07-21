import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ugc_studio.brandkit import BrandKit
from ugc_studio.guardrails import check
from ugc_studio.script import Scene, Script

BRAND = BrandKit.load()


def _script(**over):
    base = dict(id="t", title="t", persona="student", angle="a",
                scenes=[Scene(caption_bn="কোরিয়ায় পড়ুন", seconds=3)])
    base.update(over)
    return Script(**base)


def test_clean_script_passes():
    errs, _ = check(_script(), BRAND)
    assert errs == []


def test_blocks_100_percent_guarantee():
    s = _script(scenes=[Scene(caption_bn="১০০% ভিসা নিশ্চিত!", seconds=3)])
    errs, _ = check(s, BRAND)
    assert any("guarantee" in e or "absolute" in e for e in errs)


def test_blocks_english_guarantee():
    s = _script(hook_bn="We guarantee your visa")
    errs, _ = check(s, BRAND)
    assert errs


def test_blocks_98_percent_claim():
    s = _script(caption_post_bn="আমাদের ৯৮% সাকসেস রেট")
    errs, _ = check(s, BRAND)
    assert any("success-rate" in e for e in errs)


def test_blocks_escrow():
    s = _script(caption_post_bn="আপনার টাকা escrow-তে থাকবে")
    errs, _ = check(s, BRAND)
    assert any("escrow" in e for e in errs)


def test_blocks_grant_with_taka_amount():
    s = _script(caption_post_bn="কোরিয়ায় গিয়ে ১,৫০,০০০ টাকা গ্রান্ট ফেরত পাবেন")
    errs, _ = check(s, BRAND)
    # either the grant+amount rule or the 1500 rule fires — both are correct blocks
    assert errs


def test_grant_without_amount_is_ok():
    s = _script(caption_post_bn="কোরিয়ায় গিয়ে টাকা ফেরতও আসে, বিস্তারিত অফিসে")
    errs, _ = check(s, BRAND)
    assert errs == []


def test_ai_presenter_warns_disclosure():
    s = _script(ai_presenter=True)
    _, warns = check(s, BRAND)
    assert any("disclosure" in w.lower() for w in warns)


def test_consent_needed_warns():
    s = _script(needs_consent=True)
    _, warns = check(s, BRAND)
    assert any("consent" in w.lower() for w in warns)
