#!/usr/bin/env python3
"""
EasyOCR sidecar — better Bangla extraction than Tesseract on noisy scans.

Prints one JSON object per detected text region: {text, confidence, bbox}.
Feed the collected text into audit.py's student metadata.yaml (a human still
confirms extracted values — the auditor FLAGS anything unverified, never passes it).

Install (NOT installed in the repo session — heavy):
    pip install -r requirements.txt        # easyocr, pdf2image
    # PDFs also need poppler:  sudo apt install poppler-utils
CPU-only: gpu=False. First run downloads the bn+en models (~100 MB).

Usage:
    python3 easyocr_extract.py path/to/nid_scan.jpg
    python3 easyocr_extract.py path/to/bank_statement.pdf > extracted.jsonl
"""
import json
import sys


def images_from(path):
    if path.lower().endswith(".pdf"):
        try:
            from pdf2image import convert_from_path
        except ImportError:
            sys.exit("PDF input needs pdf2image + poppler: pip install pdf2image && sudo apt install poppler-utils")
        import numpy as np
        return [np.array(p) for p in convert_from_path(path, dpi=300)]
    return [path]  # EasyOCR reads image paths directly


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: easyocr_extract.py <image-or-pdf>")
    try:
        import easyocr
    except ImportError:
        sys.exit("pip install -r requirements.txt  (easyocr)")
    reader = easyocr.Reader(["bn", "en"], gpu=False)   # Bengali + English, CPU
    for page in images_from(sys.argv[1]):
        for bbox, text, conf in reader.readtext(page):
            print(json.dumps({
                "text": text,
                "confidence": round(float(conf), 3),
                "bbox": [[int(x), int(y)] for x, y in bbox],
            }, ensure_ascii=False))


if __name__ == "__main__":
    main()
