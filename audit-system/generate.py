#!/usr/bin/env python3
"""
Keystone document generator — auto-draft the derived documents.

Reads a student's metadata.yaml and produces drafts of the documents that are
mechanically derivable from their known facts:

  same_name_affidavit  — auto-generated ONLY when a name-match consistency rule
                         diverges (KUAC's hard rule), listing the exact spellings
                         and the documents they appear on.
  noc                  — the parents' No Objection affidavit.
  cover_letter         — the 5-section embassy cover letter.
  sop                  — a structured SOP scaffold (student must personalize).

Every output is a DRAFT for human review — the generator never fabricates facts
it wasn't given; missing fields are left as visible [FILL: field] markers so a
human can see exactly what to complete. This mirrors the auditor's contract:
nothing is silently invented.

Usage:
    python3 generate.py --student students/kuac-demo/ \
                        --manifest manifests/korea/kdu-global-kuac.yaml \
                        [--doc same_name_affidavit,noc,cover_letter,sop] \
                        [--out-dir students/kuac-demo/generated/]
"""
import argparse
import os
import string
import sys

import audit  # reuse manifest loading + the name-mismatch detector

HERE = os.path.dirname(os.path.abspath(__file__))
TPL_DIR = os.path.join(HERE, "templates")


class _Filler(dict):
    """string.Template mapping that turns any missing key into a visible marker
    instead of raising — so a draft always renders and shows what's incomplete."""
    def __missing__(self, key):
        return f"[FILL: {key}]"


def _fill(template_name, values):
    with open(os.path.join(TPL_DIR, template_name), encoding="utf-8") as fh:
        tpl = string.Template(fh.read())
    return tpl.safe_substitute(_Filler(values))


def _name_rules(manifest):
    return [r for r in manifest.get("consistency_rules", []) if "name" in r["id"].lower()]


def _mismatch_block(manifest, meta):
    """Build the human-readable list of diverging name spellings + their documents."""
    lines = []
    for rule in _name_rules(manifest):
        provided = {f: meta.get(f) for f in rule["fields"] if meta.get(f) not in (None, "")}
        if len({str(v) for v in provided.values()}) > 1:
            # group documents by the spelling they carry
            by_spelling = {}
            for field, val in provided.items():
                doc = field.rsplit("_", 1)[-1] if field.rsplit("_", 1)[-1] not in ("name",) else field
                # field looks like father_name_nid -> doc token 'nid'
                token = field.split("_")[-1]
                by_spelling.setdefault(str(val), []).append(token)
            who = rule["id"].replace("_match", "").replace("_kuac", "").replace("_", " ")
            lines.append(f"   **{who.title()}:**")
            for spelling, docs in by_spelling.items():
                lines.append(f"   - \"{spelling}\" — as it appears on: {', '.join(sorted(set(docs)))}")
    return "\n".join(lines) if lines else "   (no name divergence detected)"


def _values(meta, manifest):
    """Map student metadata to the union of template placeholders (best-effort;
    unknowns become [FILL: ...] markers via _Filler)."""
    father = meta.get("father_name_nid") or meta.get("sponsor_name_bank") or meta.get("father_name_academic")
    mother = meta.get("mother_name_nid") or meta.get("mother_name_academic")
    return {
        "student_name": meta.get("student_name") or meta.get("student_name_passport"),
        "passport_no": meta.get("passport_no"),
        "permanent_address": meta.get("permanent_address"),
        "deponent_name": meta.get("sponsor_name") or father,
        "deponent_nid": meta.get("sponsor_nid") or meta.get("father_nid"),
        "deponent_address": meta.get("permanent_address"),
        "father_name": father,
        "father_nid": meta.get("father_nid"),
        "mother_name": mother,
        "mother_nid": meta.get("mother_nid"),
        "child_relation": meta.get("child_relation", "son/daughter"),
        "university": manifest.get("university"),
        "program": manifest.get("program"),
        "sponsor_name": meta.get("sponsor_name") or father,
        "sponsor_relation": meta.get("sponsor_relation", "parent"),
        "student_phone": meta.get("student_phone"),
        "student_email": meta.get("student_email"),
        "ielts_score": meta.get("ielts_score"),
        "background_paragraph": meta.get("background_paragraph",
            "[FILL: academic background, accomplishments, awards, volunteer work, and any year gaps]"),
        "mismatch_block": _mismatch_block(manifest, meta),
    }


DOCS = {
    "same_name_affidavit": "same_name_affidavit.md.tmpl",
    "noc": "noc.md.tmpl",
    "cover_letter": "cover_letter.md.tmpl",
    "sop": "sop.md.tmpl",
}


def main():
    ap = argparse.ArgumentParser(description="Keystone derived-document generator")
    ap.add_argument("--student", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--doc", default="auto",
                    help="comma list of: same_name_affidavit,noc,cover_letter,sop — or 'auto'")
    ap.add_argument("--out-dir")
    args = ap.parse_args()

    manifest = audit.load_manifest(args.manifest)
    meta, _ = audit.load_student(args.student)
    values = _values(meta, manifest)

    if args.doc == "auto":
        wanted = ["noc", "cover_letter", "sop"]
        # the affidavit is generated ONLY if names actually diverge
        if audit._name_mismatch(manifest, meta):
            wanted.insert(0, "same_name_affidavit")
    else:
        wanted = [d.strip() for d in args.doc.split(",")]

    out_dir = args.out_dir or os.path.join(args.student, "generated")
    os.makedirs(out_dir, exist_ok=True)

    written = []
    for doc in wanted:
        if doc not in DOCS:
            print(f"skip unknown doc '{doc}'", file=sys.stderr); continue
        if doc == "same_name_affidavit" and not audit._name_mismatch(manifest, meta):
            print("skip same_name_affidavit — no name divergence (not needed)"); continue
        text = _fill(DOCS[doc], values)
        path = os.path.join(out_dir, f"{doc}.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        written.append(path)
        fills = text.count("[FILL:")
        note = f" ({fills} field(s) still need a human)" if fills else ""
        print(f"✅ {doc} -> {path}{note}")

    if not written:
        print("nothing generated.")
    else:
        print(f"\n{len(written)} draft(s) written to {out_dir}/. Every draft needs human review before use.")


if __name__ == "__main__":
    main()
