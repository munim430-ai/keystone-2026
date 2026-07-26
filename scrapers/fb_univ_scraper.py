#!/usr/bin/env python3
"""
fb_scraper.py — Facebook University Mention Scraper (facebook-scraper library)
Keystone Education Consultancy 2026

Scrapes public BD education agency pages + Korea study groups to rank which
Korean universities are posted about most.

Auth (pick ONE):
  1. Credentials:  --email EMAIL --password PASS
  2. Cookie file:  --cookies cookies.txt  (Netscape/JSON format)
  3. Offline/signals only (no auth): default fallback

Usage:
  python fb_scraper.py --email you@gmail.com --password yourpass
  python fb_scraper.py --cookies cookies.txt
  python fb_scraper.py  (offline signal mode — no FB account needed)

Output:
  ranked_universities.json
"""

import json, re, time, argparse, logging, sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ── BD agency pages + Korea study groups to scrape ──────────────────────────
FB_PAGES = [
    "wecareeducation",
    "jennyconsultancy",
    "roushanedu",
    "keystoneeducations",
    "hangeulbd",
    "sangen.edu",
    "koreanbangladesh",
    "studyinkoreabd",
]

FB_GROUPS = [
    "studyinkorea.bangladesh",
    "koreanstudentvisa",
    "studyabroadbangladesh",
    "bangladeshiinkorea",
]

# ── University signal scores (offline fallback + merge weight) ───────────────
SIGNALS = {
    "Kyungsung University":          95,
    "Sejong University":             90,
    "Kyung Hee University":          85,
    "Kyungdong University":          85,
    "Dongshin University":           80,
    "Kangwon National University":   78,
    "Dong-A University":             75,
    "Tongmyong University":          72,
    "Gachon University":             70,
    "Silla University":              68,
    "Hanyang University":            65,
    "Inha University":               62,
    "Sun Moon University":           60,
    "SolBridge International School":58,
    "Woosong University":            55,
    "Konkuk University":             52,
    "Konyang University":            50,
    "Dong-Eui University":           48,
    "Chungnam National University":  45,
    "Hanseo University":             42,
}

# ── Load IEQAS university list ───────────────────────────────────────────────
def load_universities(path="univ_list.json"):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    lookup = {}
    for u in data:
        en = u["english"].strip()
        ko = u["korean"].strip()
        variants = {en, ko}
        for suffix in [" University", " National University", " College",
                       " Institute", " Graduate School", "대학교", "대학"]:
            short = en.replace(suffix, "").strip()
            if len(short) > 4:
                variants.add(short)
        lookup[en] = {"record": u, "variants": list(variants)}
    log.info(f"Loaded {len(lookup)} universities")
    return data, lookup

# ── Count mentions across text corpus ───────────────────────────────────────
def count_mentions(corpus: list[str], lookup: dict) -> dict:
    combined = " ".join(corpus).lower()
    counts = defaultdict(int)
    for eng, info in lookup.items():
        for v in info["variants"]:
            counts[eng] += len(re.findall(re.escape(v.lower()), combined))
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

# ── facebook-scraper: scrape pages ──────────────────────────────────────────
def scrape_pages(pages: list[str], creds=None, cookies=None,
                 pages_limit=10, delay=3) -> list[str]:
    try:
        from facebook_scraper import get_posts
    except ImportError:
        log.error("facebook-scraper not installed: pip install facebook-scraper")
        return []

    texts = []
    auth = {}
    if creds:
        auth["credentials"] = creds
    if cookies:
        auth["cookies"] = cookies

    for page in pages:
        try:
            log.info(f"Scraping page: {page}")
            count = 0
            for post in get_posts(page, pages=pages_limit, **auth,
                                  options={"allow_extra_requests": False}):
                text = post.get("text") or post.get("post_text") or ""
                if text:
                    texts.append(text)
                    count += 1
            log.info(f"  → {count} posts from {page}")
        except Exception as e:
            log.warning(f"  Page {page} failed: {type(e).__name__}: {str(e)[:120]}")
        time.sleep(delay)

    return texts

# ── facebook-scraper: scrape groups ─────────────────────────────────────────
def scrape_groups(groups: list[str], creds=None, cookies=None,
                  pages_limit=10, delay=3) -> list[str]:
    try:
        from facebook_scraper import get_posts
    except ImportError:
        return []

    texts = []
    auth = {}
    if creds:
        auth["credentials"] = creds
    if cookies:
        auth["cookies"] = cookies

    for group in groups:
        try:
            log.info(f"Scraping group: {group}")
            count = 0
            for post in get_posts(group=group, pages=pages_limit, **auth,
                                  options={"allow_extra_requests": False}):
                text = post.get("text") or post.get("post_text") or ""
                if text:
                    texts.append(text)
                    count += 1
            log.info(f"  → {count} posts from group/{group}")
        except Exception as e:
            log.warning(f"  Group {group} failed: {type(e).__name__}: {str(e)[:120]}")
        time.sleep(delay)

    return texts

# ── Build ranked output ──────────────────────────────────────────────────────
def build_ranked(mention_counts: dict, univ_data: list,
                 signal_weight=0.3, scrape_weight=0.7,
                 scraped_total: int = 0) -> list[dict]:
    """
    Merge live scrape counts with offline signal scores.
    If no live data (scraped_total=0), use signals only (weight=1.0).
    """
    if scraped_total == 0:
        signal_weight, scrape_weight = 1.0, 0.0
        log.info("No live scrape data — using signals only")

    # Normalize scrape counts to 0–100
    max_count = max(mention_counts.values(), default=1) or 1

    all_names = set(SIGNALS) | set(k for k, v in mention_counts.items() if v > 0)
    results = []

    for name in all_names:
        scrape_norm = (mention_counts.get(name, 0) / max_count) * 100
        signal = SIGNALS.get(name, 0)
        combined = (scrape_weight * scrape_norm) + (signal_weight * signal)

        # Find matching IEQAS record
        record = next((u for u in univ_data if name in u["english"]
                       or u["english"] in name), None)
        tier = record["tier"] if record else "Unknown"
        korean = record["korean"] if record else ""

        results.append({
            "rank": 0,
            "university_en": name,
            "university_ko": korean,
            "tier": tier,
            "fb_mention_count": mention_counts.get(name, 0),
            "signal_score": signal,
            "combined_score": round(combined, 1),
            "scraped_at": datetime.utcnow().isoformat(),
            "data_source": "live+signals" if scraped_total > 0 else "signals_only",
        })

    results.sort(key=lambda x: x["combined_score"], reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1

    return results

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--email",    default=None, help="Facebook email/phone")
    ap.add_argument("--password", default=None, help="Facebook password")
    ap.add_argument("--cookies",  default=None, help="Path to cookies.txt (Netscape format)")
    ap.add_argument("--pages",    type=int, default=8,  help="FB pages to paginate per target")
    ap.add_argument("--delay",    type=int, default=4,  help="Seconds between requests")
    ap.add_argument("--out",      default="ranked_universities.json")
    ap.add_argument("--univs",    default="univ_list.json")
    args = ap.parse_args()

    univ_data, univ_lookup = load_universities(args.univs)

    creds = (args.email, args.password) if args.email and args.password else None
    cookies = args.cookies  # path string; facebook-scraper accepts file path

    corpus = []
    if creds or cookies:
        log.info("=== Live Facebook scraping mode ===")
        corpus += scrape_pages(FB_PAGES, creds=creds, cookies=cookies,
                               pages_limit=args.pages, delay=args.delay)
        corpus += scrape_groups(FB_GROUPS, creds=creds, cookies=cookies,
                                pages_limit=args.pages, delay=args.delay)
        log.info(f"Total posts collected: {len(corpus)}")
    else:
        log.info("=== No credentials — offline signal mode ===")

    mention_counts = count_mentions(corpus, univ_lookup)
    results = build_ranked(mention_counts, univ_data, scraped_total=len(corpus))

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    log.info(f"Saved {len(results)} universities to {args.out}")
    print(f"\n{'='*55}")
    print(f"  TOP 20 — {'LIVE FB DATA' if corpus else 'SIGNAL ESTIMATE'}")
    print(f"{'='*55}")
    for r in results[:20]:
        live = f"[FB:{r['fb_mention_count']:3d}]" if corpus else ""
        print(f"#{r['rank']:2d} score={r['combined_score']:5.1f} {live} "
              f"{r['tier'][:12]:12s} {r['university_en']}")

if __name__ == "__main__":
    main()
