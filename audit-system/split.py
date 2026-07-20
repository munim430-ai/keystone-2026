#!/usr/bin/env python3
"""
Keystone scan splitter — one combined PDF -> separately-named per-document PDFs.

KUAC (and most Korean universities) reject a single combined PDF and require each
document as its own file ("Send them all separately as we must organize them that
way"). Students, though, hand you one CamScanner PDF of everything. This turns
that into the required output folder in one command.

You supply a small page-map (YAML): which page range is which document. The map
uses the SAME document ids as the manifests, so the split output drops straight
into a student's files/ folder and the auditor recognizes each doc by name.

Usage:
    python3 split.py --pdf raw_scan.pdf --map students/<name>/pagemap.yaml \
                     --out students/<name>/files/

pagemap.yaml:
    # document_id: "page-range"   (1-indexed, inclusive; single page or a-b)
    passport: "1"
    academic_certificates: "2-4"
    bank_statement: "7-9"
    ...

Requires pypdf (pip install pypdf).
"""
import argparse
import os
import sys

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")
try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    sys.exit("pypdf required: pip install pypdf")


def parse_range(spec, n_pages):
    """'3' -> [2]; '2-4' -> [1,2,3] (0-indexed). Validates against page count."""
    spec = str(spec).strip()
    if "-" in spec:
        a, b = spec.split("-", 1)
        start, end = int(a), int(b)
    else:
        start = end = int(spec)
    if start < 1 or end > n_pages or start > end:
        raise ValueError(f"range '{spec}' out of bounds for a {n_pages}-page PDF")
    return list(range(start - 1, end))


def main():
    ap = argparse.ArgumentParser(description="Split one combined scan into named per-document PDFs")
    ap.add_argument("--pdf", required=True, help="the combined scan")
    ap.add_argument("--map", required=True, help="pagemap.yaml (document_id: page-range)")
    ap.add_argument("--out", required=True, help="output dir (e.g. students/<name>/files/)")
    args = ap.parse_args()

    reader = PdfReader(args.pdf)
    n = len(reader.pages)
    pagemap = yaml.safe_load(open(args.map, encoding="utf-8")) or {}
    os.makedirs(args.out, exist_ok=True)

    # validate the whole map first — never write a partial, silently-wrong split
    plans, used, errors = {}, set(), []
    for doc_id, spec in pagemap.items():
        try:
            pages = parse_range(spec, n)
        except ValueError as e:
            errors.append(f"{doc_id}: {e}")
            continue
        plans[doc_id] = pages
        used.update(pages)
    if errors:
        sys.exit("pagemap errors — nothing written:\n  - " + "\n  - ".join(errors))

    unmapped = [i + 1 for i in range(n) if i not in used]
    written = []
    for doc_id, pages in plans.items():
        w = PdfWriter()
        for p in pages:
            w.add_page(reader.pages[p])
        path = os.path.join(args.out, f"{doc_id}.pdf")
        with open(path, "wb") as fh:
            w.write(fh)
        written.append((doc_id, len(pages), path))

    for doc_id, npg, path in written:
        print(f"✅ {doc_id}: {npg} page(s) -> {path}")
    print(f"\n{len(written)} document(s) written to {args.out}")
    if unmapped:
        print(f"⚠️  pages not assigned to any document: {unmapped} "
              f"(add them to the pagemap, or confirm they're intentionally dropped)")


if __name__ == "__main__":
    main()
