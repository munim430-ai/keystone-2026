import datetime as dt

import pytest

from orchestrator import guardrails as g
from orchestrator.agents import AGENT_TOOLS


def test_no_agent_has_a_send_tool():
    # the registry import already asserts this, but pin it explicitly
    for agent, tools in AGENT_TOOLS.items():
        g.assert_no_send_tools(tools)


def test_send_tool_is_rejected():
    with pytest.raises(AssertionError):
        g.assert_no_send_tools(["fs", "wa_send"])
    with pytest.raises(AssertionError):
        g.assert_no_send_tools(["pay_invoice"])


def test_anonymize_strips_pii():
    txt = "Sania Akter, phone 01711000000, passport A19550643 applied."
    out = g.anonymize(txt, "Sania Akter")
    assert "Sania Akter" not in out
    assert "01711000000" not in out
    assert "A19550643" not in out
    assert "[Student SA]" in out


def test_assert_anonymized_raises_on_leak():
    with pytest.raises(AssertionError):
        g.assert_anonymized("contact Sania Akter now", "Sania Akter")
    with pytest.raises(AssertionError):
        g.assert_anonymized("call 01711000000", "")


def test_banned_claims():
    assert g.check_claims("আমরা ১০০% ভিসা গ্যারান্টি দিই")
    assert g.check_claims("98% success rate")
    assert g.check_claims("1500 universities")
    assert g.check_claims("your money is in escrow")
    assert g.check_claims("কোনো ভিসা, কোনো ফি") == []


def test_brand_safe_raises():
    with pytest.raises(AssertionError):
        g.assert_brand_safe("we guarantee your visa 100%")


def test_document_scope_excludes_advice():
    assert g.is_document_checklist_scope("পাসপোর্ট আর ব্যাংক স্টেটমেন্ট বাকি আছে")
    assert not g.is_document_checklist_scope("আপনি নিশ্চিত ভিসা পাবেন")


def test_survival_status_behind_and_ontrack():
    behind = g.survival_status(0, today=dt.date(2026, 8, 20))
    assert behind["on_track"] is False and behind["days_left"] == 11
    ok = g.survival_status(3, today=dt.date(2026, 9, 1))
    assert ok["on_track"] is True
