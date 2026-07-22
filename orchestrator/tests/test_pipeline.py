"""End-to-end pipeline tests on a fabricated student — no keys, no network."""
import shutil

import pytest

from orchestrator import ceo
from orchestrator.agents import instruct_agent, matcher_agent
from orchestrator.config import STUDENTS_DIR
from orchestrator.models import Job
from orchestrator.tools import db, fs

SLUG = "pytest-fixture-student"


@pytest.fixture()
def student():
    # clean slate
    shutil.rmtree(STUDENTS_DIR / SLUG, ignore_errors=True)
    meta = {"name": "Pytest Fixture", "phone": "+8801711000000",
            "source": "test", "stage": "intake"}
    fs.create_student(SLUG, meta)
    # half-complete metadata: academics known, bank blank → real MISSING/FLAGGED
    for f, v in {"student_name": "Pytest Fixture", "bachelor_cgpa": 3.4,
                 "graduation_year": 2024, "ielts_score": 5.5,
                 "bank_balance_usd": "", "sponsor_annual_income_bdt": ""}.items():
        fs.set_metadata_field(SLUG, f, v)
    for fn in ("passport.pdf", "sop.pdf"):
        (fs.student_root(SLUG) / "files" / fn).write_bytes(b"%PDF demo\n")
    yield SLUG
    shutil.rmtree(STUDENTS_DIR / SLUG, ignore_errors=True)


def test_folder_created(student):
    assert fs.exists(student)
    for d in ("docs_in", "files", "chats", "audits", "instructions"):
        assert (fs.student_root(student) / d).is_dir()
    assert fs.read_metadata_yaml(student)["bachelor_cgpa"] == 3.4


def test_matcher_ranks_and_writes(student):
    m = matcher_agent.run(student)
    assert m["top"], "expected at least one ranked university"
    # every entry has an eligibility verdict, none silently 'pass' on unknowns
    for row in m["all"]:
        assert row["eligibility"] in ("eligible", "possible", "ineligible")
    assert fs.read_match(student) is not None


def test_audit_produces_verdict(student):
    matcher_agent.run(student)
    from orchestrator.agents import audit_agent
    js = audit_agent.run(student)
    assert set(js["counts"]) >= {"VERIFIED", "FLAGGED", "MISSING"}
    # bank is blank → not READY
    assert js["ready"] is False
    assert fs.latest_audit_json(student) is not None


def test_instruct_drafts_are_pending_and_bangla(student):
    matcher_agent.run(student)
    from orchestrator.agents import audit_agent
    js = audit_agent.run(student)
    r = instruct_agent.run(student, js)
    row = [d for d in db.drafts("pending") if d["id"] == r["draft_id"]]
    assert row and row[0]["status"] == "pending"        # never auto-sent
    body = row[0]["body_bn"]
    assert "কোনো ভিসা, কোনো ফি" in body                 # brand footer present
    assert any("ঀ" <= ch <= "৿" for ch in body)  # actually Bangla


def test_full_chain_via_ceo(student):
    log = ceo.process_new_student(student)
    kinds = [l["kind"] for l in log]
    assert kinds[0] == "match" and "audit" in kinds and "instruct" in kinds
    # context bundle written
    assert (fs.student_root(student) / "context.md").exists()


def test_content_agent_anonymizes(student):
    # even if a name is passed in, the draft must not contain it
    from orchestrator.agents import content_agent
    r = content_agent.run("Sania Akter was helped; phone 01711000000", "Sania Akter")
    assert "Sania Akter" not in r["body"]
    assert "01711000000" not in r["body"]
