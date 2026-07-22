"""MatcherAgent — rank universities the student is actually eligible for.

Pulls hard eligibility gates straight from the manifest `checks` (so the match
logic and the audit logic can never drift apart), scores the student's known
profile against them, and enriches with the master list's visa-likelihood
score. Unknown fields are treated as "possible", never as a pass — same
zero-silent-error spirit as the auditor.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from ..config import MANIFEST_DIR, MASTER_LIST
from ..tools import fs
from .audit_agent import audit_mod

# manifest check type → (student metadata field, comparison)
GATES = {
    "min_gpa": "bachelor_cgpa",
    "min_score": "ielts_score",
    "max_years_since_graduation": "graduation_year",
    "min_amount_usd": "bank_balance_usd",
    "min_annual_income_bdt": "sponsor_annual_income_bdt",
}


def _manifest_paths() -> list[Path]:
    # skip abstract base manifests (e.g. _core-korea.yaml) — they are extended,
    # never applied to a student directly.
    return sorted(p for p in (MANIFEST_DIR / "korea").glob("*.yaml")
                  if not p.name.startswith("_"))


def _eval_gate(ctype: str, need, have) -> str | None:
    """Return 'pass' | 'fail' | None(unknown). Mirrors audit.run_check math."""
    if have in (None, ""):
        return None
    try:
        if ctype == "max_years_since_graduation":
            yrs = dt.date.today().year - int(have)
            return "pass" if yrs <= float(need) else "fail"
        return "pass" if float(have) >= float(need) else "fail"
    except (ValueError, TypeError):
        return None


def _master_index() -> dict:
    """Map a lowercased university keyword → master-list row (score, priority)."""
    idx = {}
    try:
        import openpyxl
        wb = openpyxl.load_workbook(MASTER_LIST, read_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        head = [str(h).strip() for h in rows[0]]
        col = {h: i for i, h in enumerate(head)}
        for r in rows[1:]:
            name = str(r[col["University / Institute"]] or "")
            key = name.lower().split("(")[0].strip()
            if key:
                idx[key] = {
                    "score": r[col.get("Visa-Likelihood Score (0-10, heuristic)", -1)],
                    "priority": r[col.get("Priority", -1)],
                    "ieqas": r[col.get("IEQAS Tier", -1)],
                }
    except Exception:
        pass
    return idx


def _score_manifest(mpath: Path, meta: dict, master: dict) -> dict:
    m = audit_mod.load_manifest(str(mpath))
    gates, fails, unknowns = [], [], []
    for doc in m.get("documents", []):
        for chk in doc.get("checks", []):
            ctype = chk.get("type")
            if ctype not in GATES or chk.get("value") in (None, ""):
                continue
            field = GATES[ctype]
            verdict = _eval_gate(ctype, chk["value"], meta.get(field))
            g = {"gate": ctype, "field": field, "need": chk["value"],
                 "have": meta.get(field), "verdict": verdict or "unknown"}
            gates.append(g)
            if verdict == "fail":
                fails.append(g)
            elif verdict is None:
                unknowns.append(g)

    uni_key = m["university"].lower().split("(")[0].strip()
    mrow = next((v for k, v in master.items() if k in uni_key or uni_key in k), {})
    vscore = mrow.get("score")
    vscore = vscore if isinstance(vscore, (int, float)) else 0

    eligibility = "ineligible" if fails else ("possible" if unknowns else "eligible")
    # rank: eligible > possible > ineligible, then higher visa-likelihood, fewer unknowns
    rank_key = ({"eligible": 0, "possible": 1, "ineligible": 2}[eligibility],
                -vscore, len(unknowns))
    return {
        "manifest": m["id"],
        "manifest_path": str(mpath),
        "university": m["university"],
        "program": m["program"],
        "visa_type": m.get("visa_type", ""),
        "eligibility": eligibility,
        "visa_likelihood": vscore,
        "priority": mrow.get("priority"),
        "gate_fails": [f"{g['field']} {g['have']} < need {g['need']}" for g in fails],
        "unknowns": [g["field"] for g in unknowns],
        "_rank": rank_key,
    }


def run(slug: str, top_n: int = 5) -> dict:
    meta = fs.read_metadata_yaml(slug)
    master = _master_index()
    scored = [_score_manifest(p, meta, master) for p in _manifest_paths()]
    scored.sort(key=lambda x: x.pop("_rank"))
    match = {
        "student": slug,
        "generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "profile_used": {k: meta.get(k) for k in set(GATES.values()) if meta.get(k) not in (None, "")},
        "top": scored[:top_n],
        "all": scored,
    }
    fs.write_match(slug, match)
    return match
