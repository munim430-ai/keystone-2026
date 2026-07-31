#!/usr/bin/env python3
"""
Keystone page classifier — proposes a pagemap.yaml for split.py by OCR-reading
each page of a combined scan and keyword-matching it against known document types.

Design principle (same one audit.py uses): never silently guess. Every page lands
in one of three buckets:

    CONFIDENT   — top-scoring doc_id has a clear lead over the runner-up
    AMBIGUOUS   — top two candidates are tied or too close to call
    UNRECOGNIZED — nothing scored above the minimum hit threshold (often a bare
                   photo page, a blank separator, or a document type with no
                   signature yet in manifests/document_signatures.yaml)

Only CONFIDENT pages go into the proposed pagemap automatically. AMBIGUOUS and
UNRECOGNIZED pages are listed separately for a human to assign by hand — the tool
never writes a guess into the pagemap it isn't confident about.

OCR engine: Tesseract (ben+eng) by default — light enough for a local PC, no GPU,
no ~2GB torch download. Pass --engine easyocr to use the sidecar's EasyOCR reader
instead (better on noisy/rotated scans, heavier install) for a second pass over
just the pages Tesseract left AMBIGUOUS/UNRECOGNIZED.

Usage:
    python3 classify.py --pdf raw_scan.pdf --out students/<name>/pagemap.yaml
    python3 classify.py --pdf raw_scan.pdf --out students/<name>/pagemap.yaml \
        --engine easyocr --recheck-uncertain-only   # second pass, Tesseract's leftovers only

Requires: pytesseract, pdf2image, pyyaml, and the system packages
tesseract-ocr + tesseract-ocr-ben + poppler-utils.
    sudo apt install tesseract-ocr tesseract-ocr-ben tesseract-ocr-eng poppler-utils
    pip install pytesseract pdf2image pyyaml
"""
import argparse
import os
import sys

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

HERE = os.path.dirname(os.path.abspath(__file__))
SIGNATURES_PATH = os.path.join(HERE, "manifests", "document_signatures.yaml")

CONFIDENT, AMBIGUOUS, UNRECOGNIZED = "CONFIDENT", "AMBIGUOUS", "UNRECOGNIZED"


def load_signatures():
    with open(SIGNATURES_PATH, encoding="utf-8") as fh:
        sig = yaml.safe_load(fh) or {}
    return {k: [str(kw) for kw in (v or [])] for k, v in sig.items()}


def ocr_page_tesseract(image):
    import pytesseract
    return pytesseract.image_to_string(image, lang="ben+eng")


def ocr_page_easyocr(image, reader):
    import numpy as np
    results = reader.readtext(np.array(image))
    return "\n".join(text for _, text, _ in results)


def score_page(text, signatures):
    """Return sorted [(doc_id, hits), ...] — hits = count of matched keywords."""
    low = text.lower()
    scores = []
    for doc_id, keywords in signatures.items():
        if not keywords:
            continue
        hits = sum(1 for kw in keywords if kw.lower() in low)
        if hits:
            scores.append((doc_id, hits))
    return sorted(scores, key=lambda x: -x[1])


def classify_scores(scores, min_hits=1, min_lead=1):
    """Decide CONFIDENT / AMBIGUOUS / UNRECOGNIZED from a sorted score list."""
    if not scores or scores[0][1] < min_hits:
        return UNRECOGNIZED, None
    if len(scores) == 1 or scores[0][1] - scores[1][1] >= min_lead:
        return CONFIDENT, scores[0][0]
    return AMBIGUOUS, None


def images_from_pdf(path, dpi=300):
    try:
        from pdf2image import convert_from_path
    except ImportError:
        sys.exit("pdf2image required: pip install pdf2image  (also needs poppler-utils)")
    return convert_from_path(path, dpi=dpi)


def build_pagemap(page_results):
    """Collapse a list of (page_num, doc_id_or_None) into contiguous ranges.
    A doc_id repeated in a SECOND, non-contiguous run gets a __2, __3 suffix so it
    is never silently merged with the first run under one filename."""
    pagemap = {}
    seen_counts = {}
    i = 0
    n = len(page_results)
    while i < n:
        page, doc_id = page_results[i]
        if doc_id is None:
            i += 1
            continue
        j = i
        while j + 1 < n and page_results[j + 1][1] == doc_id:
            j += 1
        start, end = page_results[i][0], page_results[j][0]
        seen_counts[doc_id] = seen_counts.get(doc_id, 0) + 1
        key = doc_id if seen_counts[doc_id] == 1 else f"{doc_id}__{seen_counts[doc_id]}"
        pagemap[key] = str(start) if start == end else f"{start}-{end}"
        i = j + 1
    return pagemap


def main():
    ap = argparse.ArgumentParser(description="Propose a pagemap.yaml by OCR-classifying each page")
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--out", required=True, help="pagemap.yaml to write (CONFIDENT pages only)")
    ap.add_argument("--report", help="also write a full per-page classification report (.md)")
    ap.add_argument("--engine", choices=["tesseract", "easyocr"], default="tesseract")
    ap.add_argument("--min-hits", type=int, default=1, help="minimum keyword hits to consider a match at all")
    ap.add_argument("--min-lead", type=int, default=1, help="minimum hit-count lead over the runner-up to call it CONFIDENT")
    ap.add_argument("--dpi", type=int, default=300)
    args = ap.parse_args()

    signatures = load_signatures()
    if not signatures:
        sys.exit(f"no signatures loaded from {SIGNATURES_PATH}")

    print(f"Rendering {args.pdf} at {args.dpi} DPI...", file=sys.stderr)
    images = images_from_pdf(args.pdf, dpi=args.dpi)
    print(f"{len(images)} page(s). OCR engine: {args.engine}", file=sys.stderr)

    easyocr_reader = None
    if args.engine == "easyocr":
        try:
            import easyocr
        except ImportError:
            sys.exit("easyocr not installed: pip install -r sidecar/requirements.txt")
        easyocr_reader = easyocr.Reader(["bn", "en"], gpu=False)

    page_results = []       # (page_num, doc_id or None) -- only CONFIDENT pages get a doc_id
    report_rows = []        # for the human-readable report
    for idx, image in enumerate(images, start=1):
        text = (ocr_page_easyocr(image, easyocr_reader) if easyocr_reader
                else ocr_page_tesseract(image))
        scores = score_page(text, signatures)
        state, doc_id = classify_scores(scores, args.min_hits, args.min_lead)
        page_results.append((idx, doc_id if state == CONFIDENT else None))
        report_rows.append((idx, state, doc_id, scores[:3], len(text.strip())))
        icon = {"CONFIDENT": "✅", "AMBIGUOUS": "⚠️", "UNRECOGNIZED": "❓"}[state]
        top = ", ".join(f"{d}={h}" for d, h in scores[:3]) or "no keyword hits"
        print(f"{icon} page {idx:>3}: {state:<12} {doc_id or '-':<28} ({top})", file=sys.stderr)

    pagemap = build_pagemap(page_results)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("# Proposed by classify.py — CONFIDENT pages only. Review before running split.py.\n")
        fh.write("# AMBIGUOUS/UNRECOGNIZED pages are listed in the report, not here — add them by hand.\n")
        yaml.safe_dump(pagemap, fh, allow_unicode=True, sort_keys=True)

    n_confident = sum(1 for r in report_rows if r[1] == CONFIDENT)
    n_ambiguous = sum(1 for r in report_rows if r[1] == AMBIGUOUS)
    n_unrecognized = sum(1 for r in report_rows if r[1] == UNRECOGNIZED)
    print(f"\n{n_confident} confident, {n_ambiguous} ambiguous, {n_unrecognized} unrecognized "
          f"out of {len(images)} page(s).", file=sys.stderr)
    print(f"Proposed pagemap -> {args.out} ({len(pagemap)} document(s) mapped)", file=sys.stderr)
    if n_ambiguous or n_unrecognized:
        print("⚠️  Not every page was auto-mapped — resolve AMBIGUOUS/UNRECOGNIZED pages by hand "
              "before running split.py, or re-run with --engine easyocr for a second opinion.", file=sys.stderr)

    if args.report:
        lines = ["# Page Classification Report", "", f"Source: `{args.pdf}` ({len(images)} pages, engine={args.engine})", ""]
        lines.append("| Page | State | Assigned doc_id | Top candidates | OCR chars |")
        lines.append("|---|---|---|---|---|")
        for page, state, doc_id, scores, nchars in report_rows:
            icon = {"CONFIDENT": "✅", "AMBIGUOUS": "⚠️", "UNRECOGNIZED": "❓"}[state]
            cand = ", ".join(f"{d} ({h})" for d, h in scores) or "—"
            lines.append(f"| {page} | {icon} {state} | {doc_id or '—'} | {cand} | {nchars} |")
        with open(args.report, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print(f"Full report -> {args.report}", file=sys.stderr)


if __name__ == "__main__":
    main()
