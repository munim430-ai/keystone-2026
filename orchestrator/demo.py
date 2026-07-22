"""End-to-end demo on a FABRICATED messy student — zero keys, zero spend.

Walks intake → match → audit → Bangla draft → board, printing each step, so the
founder can see the whole machine work before wiring any real service. Uses a
deliberately half-complete metadata (the realistic case: some fields known, some
blank) so the audit produces real MISSING/FLAGGED items and a real Bangla draft.
"""
from __future__ import annotations

from . import ceo
from .tools import db, fs

DEMO_SLUG = "demo-fabricated-student"

# A realistic messy profile: strong academics known, bank/sponsor half-missing.
DEMO_META = {
    "student_name": "Fabricated Demo Student",
    "hsc_gpa": 3.83,
    "bachelor_cgpa": 3.40,
    "graduation_year": 2024,
    "ielts_score": 5.0,
    "bank_balance_usd": "",          # blank → FLAGGED (the real-world gap)
    "bank_history_months": "",
    "sponsor_annual_income_bdt": "",
    "student_name_passport": "Fabricated Demo Student",
    "student_name_nid": "Fabricated Demo Student",
    "human_signoffs": [],
}


def run_demo() -> int:
    print("=" * 66)
    print("KEYSTONE CEO ORCHESTRATOR — end-to-end demo ($0, no keys, no send)")
    print("=" * 66)

    # 1) intake — create the folder + card
    meta = {"name": "Fabricated Demo Student", "phone": "+8801711000000",
            "source": "demo", "stage": "intake"}
    fs.create_student(DEMO_SLUG, meta)
    for f, v in DEMO_META.items():
        fs.set_metadata_field(DEMO_SLUG, f, v)
    # simulate a couple of messy uploads present in files/ so the auditor sees them
    fdir = fs.student_root(DEMO_SLUG) / "files"
    for fn in ("passport.pdf", "academic_certificates.pdf", "sop.pdf"):
        (fdir / fn).write_bytes(b"%PDF-1.4 demo\n")
    db.upsert_student(DEMO_SLUG, stage="intake", name=meta["name"])
    print(f"\n[1] intake         → students/{DEMO_SLUG}/ created (3 messy files, half-blank metadata)")

    # 2) run the chain
    print("[2] CEO chain      → match → audit → instruct")
    log = ceo.process_new_student(DEMO_SLUG)
    for l in log:
        print(f"      [{l['kind']:8s}] {l.get('summary') or l.get('data','ok')}")

    # 3) show the produced Bangla draft (pending — NOT sent)
    pend = db.drafts("pending")
    student_drafts = [d for d in pend if d.get("student") == DEMO_SLUG]
    print(f"\n[3] Bangla draft   → {len(student_drafts)} pending in the approval queue (nothing sent):\n")
    if student_drafts:
        print("    " + student_drafts[-1]["body_bn"].replace("\n", "\n    "))

    # 4) survival banner
    print(f"\n[4] survival clock → {ceo.CEO().survival()['banner']}")
    print("\nDone. Board: `python -m orchestrator.cli board` · "
          "Drafts: `python -m orchestrator.cli drafts`")
    print("Nothing was sent, posted, or paid for.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_demo())
