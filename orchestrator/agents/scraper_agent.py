"""ScraperAgent — B2B institute list enrichment + competitor page insight.

Wraps the existing scrapers/ielts_scraper.py output (data/IELTS_Partners_Tier2.csv)
and can pull public competitor pages via the read-only fetcher. B2B-only:
never touches student PII or Facebook groups/profiles (hard guardrail).
Returns insights (and, when asked, feeds the content agent) — it does not post.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from ..config import REPO_DIR
from ..tools import search

B2B_CSV = REPO_DIR / "data" / "IELTS_Partners_Tier2.csv"


def b2b_summary() -> dict:
    """District coverage of the 859-center B2B list — the call-plan ammunition."""
    if not B2B_CSV.exists():
        return {"error": f"{B2B_CSV} not found"}
    by_district = Counter()
    total = 0
    with open(B2B_CSV, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            total += 1
            by_district[(row.get("Location (District)") or "").strip() or "?"] += 1
    return {"total_centers": total,
            "districts": dict(by_district.most_common()),
            "top_10": by_district.most_common(10)}


def competitor_snapshot(urls: list[str]) -> dict:
    """Fetch public competitor pages and report crude signals (length, pricing
    mentions). Read-only, public pages only — insight, not scraping-for-PII."""
    out = []
    for u in urls:
        try:
            html = search.fetch(u)
            low = html.lower()
            out.append({"url": u, "bytes": len(html),
                        "mentions_price": any(k in low for k in ("৳", "taka", "fee", "tk ")),
                        "mentions_korea": "korea" in low})
        except Exception as e:
            out.append({"url": u, "error": str(e)})
    return {"pages": out}


def run(mode: str = "b2b", urls: list[str] | None = None) -> dict:
    if mode == "competitor" and urls:
        return competitor_snapshot(urls)
    return b2b_summary()
