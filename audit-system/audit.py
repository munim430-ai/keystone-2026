#!/usr/bin/env python3
"""
Keystone document auditor — the zero-SILENT-error engine.

Design principle: the machine never says PASS on anything it could not mechanically
verify. Every required item lands in exactly one of three states:

    VERIFIED  — present AND every machine-checkable rule passed (evidence attached)
    FLAGGED   — present but a rule needs a human (human_verify, or a field the
                student metadata did not supply, or a below-confidence extraction)
    MISSING   — not present, or a definitive rule failure (FAILED is a MISSING subtype)

A file is only "ready to submit" when ZERO items are MISSING and ZERO items are
FLAGGED without a recorded human sign-off. The engine guarantees nothing is
forgotten; a human resolves the small FLAGGED pile. That is how you approach
zero real-world error — not by trusting OCR, but by never auto-passing what
couldn't be proven.

Usage:
    python3 audit.py --manifest manifests/korea/kyungsung-bachelor.yaml \
                     --student students/ariful/ \
                     [--report-dir out/] [--json]

The student folder must contain:
    metadata.yaml   — extracted/known facts (see students/_TEMPLATE/metadata.yaml)
    files/          — the actual document files, one filename containing each
                      document id (e.g. passport.pdf, bank_statement.pdf)

Exit code 0 only when the file is submit-ready; 2 otherwise. So CI / a pre-submit
hook can literally block submission on a non-clean audit.
"""
import argparse
import datetime as dt
import json
import os
import sys

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST_DIR = os.path.join(HERE, "manifests")
SCHEMA_PATH = os.path.join(MANIFEST_DIR, "schema.json")

VERIFIED, FLAGGED, MISSING = "VERIFIED", "FLAGGED", "MISSING"
ICON = {VERIFIED: "✅", FLAGGED: "⚠️", MISSING: "❌"}


# ------------------------------------------------------------------ manifest load
def _load_yaml(path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def validate_manifest_file(path):
    """Validate one manifest against the JSON schema so rule typos fail loudly."""
    data = _load_yaml(path)
    try:
        import jsonschema
    except ImportError:
        return data, ["jsonschema not installed — skipped schema validation (pip install jsonschema)"]
    schema = json.load(open(SCHEMA_PATH, encoding="utf-8"))
    errs = []
    for e in jsonschema.Draft7Validator(schema).iter_errors(data):
        errs.append(f"{'/'.join(str(p) for p in e.path)}: {e.message}")
    return data, errs


def _find_manifest_by_id(mid):
    for root, _, files in os.walk(MANIFEST_DIR):
        for f in files:
            if f.endswith((".yaml", ".yml")):
                p = os.path.join(root, f)
                d = _load_yaml(p)
                if d.get("id") == mid:
                    return p
    return None


def load_manifest(path):
    """Load a manifest, merging its `extends` base. Child docs override base docs
    by id; child consistency_rules append to the base's."""
    data, errs = validate_manifest_file(path)
    if errs:
        raise ValueError("Manifest failed schema validation:\n  - " + "\n  - ".join(errs))
    base_id = data.get("extends")
    if not base_id:
        return data
    base_path = _find_manifest_by_id(base_id)
    if not base_path:
        raise ValueError(f"extends: '{base_id}' — base manifest not found")
    base = load_manifest(base_path)
    docs = {d["id"]: d for d in base.get("documents", [])}
    for d in data.get("documents", []):
        docs[d["id"]] = d  # child overrides base by id
    merged = dict(base)
    merged.update({k: v for k, v in data.items() if k not in ("documents", "consistency_rules")})
    merged["documents"] = list(docs.values())
    merged["consistency_rules"] = base.get("consistency_rules", []) + data.get("consistency_rules", [])
    return merged


# ------------------------------------------------------------------ student load
def load_student(folder):
    meta_path = os.path.join(folder, "metadata.yaml")
    meta = _load_yaml(meta_path) if os.path.exists(meta_path) else {}
    files_dir = os.path.join(folder, "files")
    present = []
    if os.path.isdir(files_dir):
        present = [f for f in os.listdir(files_dir) if not f.startswith(".")]
    return meta or {}, present


def _doc_present(doc_id, present_files):
    """A document is present if any filename contains its id (case-insensitive)."""
    did = doc_id.lower()
    return any(did in f.lower() for f in present_files)


def _required(doc, meta):
    r = doc.get("required", True)
    if isinstance(r, bool):
        return r, None
    if isinstance(r, str) and r.startswith("if:"):
        cond = r[3:].strip()
        return bool(meta.get(cond, False)), cond
    return True, None


# ------------------------------------------------------------------ checks
def _months_between(d1, d2):
    return (d1.year - d2.year) * 12 + (d1.month - d2.month)


def run_check(check, meta):
    """Return (state, message). Missing field -> FLAGGED (never silently pass)."""
    ctype = check["type"]
    if ctype == "human_verify":
        return FLAGGED, "needs human review: " + check.get("description", "manual check")
    field = check.get("field")
    val = meta.get(field) if field else None
    if field and val in (None, ""):
        return FLAGGED, f"field '{field}' not provided in metadata — cannot verify {ctype}"
    today = dt.date.today()

    def as_date(v):
        return v if isinstance(v, dt.date) else dt.date.fromisoformat(str(v))

    try:
        if ctype == "min_validity_months":
            m = _months_between(as_date(val), today)
            return (VERIFIED, f"valid {m} months (>= {check['value']})") if m >= check["value"] \
                else (MISSING, f"only {m} months validity (< {check['value']})")
        if ctype == "max_age_days":
            age = (today - as_date(val)).days
            return (VERIFIED, f"{age} days old (<= {check['value']})") if age <= check["value"] \
                else (MISSING, f"{age} days old (> {check['value']} — too old, re-issue)")
        if ctype == "max_years_since_graduation":
            yrs = today.year - int(val)
            return (VERIFIED, f"graduated {yrs}y ago (<= {check['value']})") if yrs <= check["value"] \
                else (MISSING, f"graduated {yrs}y ago (> {check['value']} — ineligible)")
        num_checks = {
            "min_amount_usd": ("USD", ">="), "min_history_months": ("months", ">="),
            "min_score": ("score", ">="), "min_gpa": ("GPA", ">="),
            "min_annual_income_bdt": ("BDT", ">="),
        }
        if ctype in num_checks:
            unit, _ = num_checks[ctype]
            return (VERIFIED, f"{val} {unit} (>= {check['value']})") if float(val) >= float(check["value"]) \
                else (MISSING, f"{val} {unit} (< {check['value']} — shortfall)")
        if ctype == "exact_dimensions_mm":
            return (VERIFIED, f"{val} == {check['value']}") if str(val) == str(check["value"]) \
                else (MISSING, f"{val} != required {check['value']}")
        if ctype == "field_present":
            return (VERIFIED, f"{field} present") if val else (MISSING, f"{field} absent")
    except (ValueError, TypeError) as e:
        return FLAGGED, f"could not evaluate {ctype} on '{val}': {e}"
    return FLAGGED, f"unknown check type {ctype} — human review"


def worst(states):
    for s in (MISSING, FLAGGED, VERIFIED):
        if s in states:
            return s
    return VERIFIED


# ------------------------------------------------------------------ audit
def audit(manifest, meta, present_files):
    signoffs = set(meta.get("human_signoffs", []))
    results = []
    for doc in manifest["documents"]:
        req, cond = _required(doc, meta)
        if not req:
            results.append({"doc": doc["id"], "name": doc["name"], "state": "SKIPPED",
                            "required": False, "messages": [f"not required (condition: {cond})" if cond else "optional"]})
            continue
        present = _doc_present(doc["id"], present_files)
        msgs, states = [], []
        if not present:
            results.append({"doc": doc["id"], "name": doc["name"], "state": MISSING,
                            "required": True, "processing": doc.get("processing", "none"),
                            "messages": [f"document not found in files/ (need: {doc['name']})"]})
            continue
        if doc.get("processing", "none") != "none":
            fld = f"{doc['id']}_processing_done"
            if meta.get(fld) is True:
                states.append(VERIFIED); msgs.append(f"processing '{doc['processing']}' confirmed done")
            else:
                states.append(FLAGGED)
                msgs.append(f"confirm processing chain '{doc['processing']}' completed (set {fld}: true)")
        for chk in doc.get("checks", []):
            st, m = run_check(chk, meta)
            # human_verify satisfied if a matching sign-off is recorded
            if st == FLAGGED and chk.get("type") == "human_verify" and doc["id"] in signoffs:
                st, m = VERIFIED, "human sign-off recorded: " + m
            states.append(st); msgs.append(m)
        state = worst(states) if states else VERIFIED
        results.append({"doc": doc["id"], "name": doc["name"], "state": state,
                        "required": True, "processing": doc.get("processing", "none"), "messages": msgs})

    # consistency rules
    consistency = []
    for rule in manifest.get("consistency_rules", []):
        vals = {f: meta.get(f) for f in rule["fields"]}
        provided = {f: v for f, v in vals.items() if v not in (None, "")}
        if len(provided) < 2:
            consistency.append({"rule": rule["id"], "state": FLAGGED,
                                "message": f"only {len(provided)}/{len(rule['fields'])} fields provided — cannot cross-check: {rule['description']}"})
            continue
        norm = (lambda s: str(s).lower()) if rule.get("match") == "exact_case_insensitive" else str
        uniq = {norm(v) for v in provided.values()}
        if len(uniq) == 1:
            consistency.append({"rule": rule["id"], "state": VERIFIED,
                                "message": f"all match ({list(provided.values())[0]!r}): {rule['description']}"})
        else:
            consistency.append({"rule": rule["id"], "state": MISSING,
                                "message": f"MISMATCH {provided}: {rule['description']}"})
    return results, consistency


# ------------------------------------------------------------------ report
def render_report(manifest, results, consistency, meta):
    counts = {VERIFIED: 0, FLAGGED: 0, MISSING: 0, "SKIPPED": 0}
    for r in results:
        counts[r["state"]] = counts.get(r["state"], 0) + 1
    for c in consistency:
        counts[c["state"]] = counts.get(c["state"], 0) + 1
    ready = counts[MISSING] == 0 and counts[FLAGGED] == 0
    lines = []
    lines.append(f"# Document Audit — {meta.get('student_name', 'UNKNOWN STUDENT')}")
    lines.append("")
    lines.append(f"**Target:** {manifest['university']} — {manifest['program']} ({manifest['visa_type']})")
    lines.append(f"**Manifest:** `{manifest['id']}` (source verified {manifest['verified_date']})")
    lines.append(f"**Audited:** {dt.date.today().isoformat()}")
    lines.append("")
    verdict = "✅ **READY TO SUBMIT**" if ready else "⛔ **NOT READY** — resolve every item below first"
    lines.append(f"## Verdict: {verdict}")
    lines.append("")
    lines.append(f"{ICON[VERIFIED]} Verified: {counts[VERIFIED]} &nbsp; "
                 f"{ICON[FLAGGED]} Flagged (need human): {counts[FLAGGED]} &nbsp; "
                 f"{ICON[MISSING]} Missing/Failed: {counts[MISSING]} &nbsp; "
                 f"➖ Skipped (n/a): {counts['SKIPPED']}")
    lines.append("")
    lines.append("> The file is submit-ready ONLY when Flagged = 0 and Missing = 0. "
                 "Flagged items are not failures — they are checks the machine cannot make alone; "
                 "a human must verify and record a sign-off. Nothing here ever auto-passes.")
    lines.append("")
    lines.append("## Documents")
    lines.append("")
    lines.append("| State | Document | Processing | Notes |")
    lines.append("|---|---|---|---|")
    order = {MISSING: 0, FLAGGED: 1, VERIFIED: 2, "SKIPPED": 3}
    for r in sorted(results, key=lambda x: order.get(x["state"], 9)):
        icon = ICON.get(r["state"], "➖")
        note = "<br>".join(r["messages"])
        lines.append(f"| {icon} {r['state']} | {r['name']} | {r.get('processing','-')} | {note} |")
    lines.append("")
    lines.append("## Consistency Rules")
    lines.append("")
    lines.append("| State | Rule | Detail |")
    lines.append("|---|---|---|")
    for c in sorted(consistency, key=lambda x: order.get(x["state"], 9)):
        lines.append(f"| {ICON.get(c['state'],'?')} {c['state']} | {c['rule']} | {c['message']} |")
    lines.append("")
    if not ready:
        lines.append("## What to do next")
        for r in results:
            if r["state"] == MISSING:
                lines.append(f"- ❌ **{r['name']}** — {'; '.join(r['messages'])}")
        for c in consistency:
            if c["state"] == MISSING:
                lines.append(f"- ❌ **{c['rule']}** — {c['message']}")
        for r in results:
            if r["state"] == FLAGGED:
                lines.append(f"- ⚠️ **{r['name']}** — {'; '.join(r['messages'])} "
                             f"(after verifying, add `{r['doc']}` to human_signoffs in metadata.yaml)")
        for c in consistency:
            if c["state"] == FLAGGED:
                lines.append(f"- ⚠️ **{c['rule']}** — {c['message']}")
    return "\n".join(lines), ready, counts


# ------------------------------------------------------------------ cli
def main():
    ap = argparse.ArgumentParser(description="Keystone zero-silent-error document auditor")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--student", required=True)
    ap.add_argument("--report-dir")
    ap.add_argument("--json", action="store_true", help="also emit a machine-readable JSON report")
    args = ap.parse_args()

    manifest = load_manifest(args.manifest)
    meta, present = load_student(args.student)
    results, consistency = audit(manifest, meta, present)
    report, ready, counts = render_report(manifest, results, consistency, meta)

    print(report)
    if args.report_dir:
        os.makedirs(args.report_dir, exist_ok=True)
        stem = f"{meta.get('student_name','student').replace(' ','_')}_{manifest['id']}"
        with open(os.path.join(args.report_dir, stem + ".md"), "w", encoding="utf-8") as fh:
            fh.write(report)
        if args.json:
            with open(os.path.join(args.report_dir, stem + ".json"), "w", encoding="utf-8") as fh:
                json.dump({"ready": ready, "counts": counts, "documents": results,
                           "consistency": consistency, "manifest": manifest["id"]}, fh, indent=2, default=str)
    sys.exit(0 if ready else 2)


if __name__ == "__main__":
    main()
