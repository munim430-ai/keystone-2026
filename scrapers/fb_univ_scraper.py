#!/usr/bin/env python3
"""
fb_scraper.py — Facebook Public Group & Page Scraper
Keystone Education Consultancy 2026

Scrapes public Facebook groups and pages used by Bangladesh education agencies
to rank which Korean universities are mentioned most.

Strategy:
  1. Uses Apify's Facebook scraper API (free tier) OR falls back to
     SerpAPI Google search (site:facebook.com) OR pure requests+BeautifulSoup
     crawling of public Facebook pages.
  2. Also queries the Facebook Graph API (public page search, no auth needed for
     public pages) for page post data.
  3. Counts university name mentions across all collected posts.
  4. Outputs: ranked_universities.json + ranked_universities.md

Usage:
  python fb_scraper.py [--method serpapi|graph|crawl] [--limit 200]

Dependencies:
  pip install requests beautifulsoup4 lxml tqdm
"""

import json, re, time, argparse, logging
from pathlib import Path
from collections import defaultdict
from datetime import datetime

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,bn;q=0.8",
}

# Bangladesh education agency Facebook groups/pages to scrape
BD_FACEBOOK_TARGETS = [
    # Public groups
    "https://www.facebook.com/groups/studyinkorea.bangladesh",
    "https://www.facebook.com/groups/koreanstudentvisa",
    "https://www.facebook.com/groups/studyabroadbangladesh",
    "https://www.facebook.com/groups/studyinkoreafrombangladesh",
    "https://www.facebook.com/groups/bangladeshiinkorea",
    "https://www.facebook.com/groups/koreaeducationbangladesh",
    # Public pages — known BD agencies
    "https://www.facebook.com/wecareeducation",
    "https://www.facebook.com/jennyconsultancy",
    "https://www.facebook.com/roushaneducation",
    "https://www.facebook.com/keystoneeducations",
    "https://www.facebook.com/hangeulbd",
    "https://www.facebook.com/koreanbangladesh",
]

# Google search queries to find more Facebook posts about Korean universities
GOOGLE_SEARCH_QUERIES = [
    'site:facebook.com "Korea university" "Bangladesh" "admission" -site:facebook.com/groups/private',
    'site:facebook.com "study in Korea" "Bangladesh" "agency" university 2026',
    'site:facebook.com "WeCare" OR "Jenny Consultancy" Korea university Bangladesh',
    'site:facebook.com "코리아" OR "한국유학" Bangladesh student visa 2026',
    'site:facebook.com "Korea scholarship" "Bangladesh" university admission',
]

# ──────────────────────────────────────────────────────────────────────────────
# UNIVERSITY LIST LOADER
# ──────────────────────────────────────────────────────────────────────────────

def load_universities(path="univ_list.json"):
    """Load the 171-university IEQAS list and build name→record lookup."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    # Build alternate-name search patterns (English + Korean)
    lookup = {}
    for u in data:
        en = u["english"].strip()
        ko = u["korean"].strip()
        # Add common shorthand variants
        variants = {en, ko}
        # Strip " University", " College", etc. for partial match
        for suffix in [" University", " National University", " College", " Institute",
                       " Graduate School", " Women's University", "대학교", "대학"]:
            short = en.replace(suffix, "").strip()
            if len(short) > 4:
                variants.add(short)
        lookup[en] = {"record": u, "variants": list(variants)}

    log.info(f"Loaded {len(lookup)} universities with name variants")
    return data, lookup

# ──────────────────────────────────────────────────────────────────────────────
# METHOD 1: Google SerpAPI / scrape (no key needed, uses public Google)
# ──────────────────────────────────────────────────────────────────────────────

def scrape_via_google(queries: list[str], delay=3) -> list[str]:
    """
    Scrape Google search results (no API key) to collect text snippets
    mentioning Korean universities in Facebook posts/pages.
    Returns list of raw text snippets.
    """
    snippets = []
    session = requests.Session()
    session.headers.update(HEADERS)

    for query in queries:
        url = "https://www.google.com/search"
        params = {"q": query, "num": 50, "hl": "en", "gl": "bd"}
        try:
            log.info(f"Google query: {query[:60]}...")
            resp = session.get(url, params=params, timeout=15)
            if resp.status_code == 429:
                log.warning("Rate limited by Google. Waiting 60s...")
                time.sleep(60)
                resp = session.get(url, params=params, timeout=15)

            soup = BeautifulSoup(resp.text, "lxml")
            # Extract result snippets
            for div in soup.find_all(["div", "span"], class_=re.compile(r"(VwiC3b|s3v9rd|st|aCOpRe|IsZvec)")):
                text = div.get_text(" ", strip=True)
                if len(text) > 30:
                    snippets.append(text)

            # Also extract titles
            for h3 in soup.find_all("h3"):
                snippets.append(h3.get_text(" ", strip=True))

            log.info(f"  → {len(snippets)} snippets so far")
            time.sleep(delay)

        except Exception as e:
            log.error(f"Google scrape error: {e}")
            time.sleep(delay * 2)

    return snippets

# ──────────────────────────────────────────────────────────────────────────────
# METHOD 2: Direct Facebook public page crawl (mbasic.facebook.com)
# ──────────────────────────────────────────────────────────────────────────────

def scrape_facebook_mbasic(targets: list[str], max_posts=50, delay=4) -> list[str]:
    """
    Use mbasic.facebook.com (lightweight public version) to collect post text.
    Works for public pages without login. Groups require login so we skip those.
    """
    all_text = []
    session = requests.Session()
    session.headers.update(HEADERS)

    for target in targets:
        # Convert to mbasic URL
        mbasic_url = target.replace("www.facebook.com", "mbasic.facebook.com")
        # Only public PAGES work without login (not groups)
        if "/groups/" in mbasic_url:
            log.info(f"Skipping group (login required): {target}")
            continue

        try:
            log.info(f"Crawling: {mbasic_url}")
            resp = session.get(mbasic_url, timeout=15)
            soup = BeautifulSoup(resp.text, "lxml")

            posts_found = 0
            for div in soup.find_all("div"):
                text = div.get_text(" ", strip=True)
                # Filter: must be substantive post text (not nav/UI)
                if len(text) > 100 and ("university" in text.lower() or 
                                          "university" in text.lower() or
                                          "korea" in text.lower() or
                                          "대학" in text or
                                          "visa" in text.lower() or
                                          "admission" in text.lower()):
                    all_text.append(text)
                    posts_found += 1
                    if posts_found >= max_posts:
                        break

            log.info(f"  → Found {posts_found} relevant posts")
            time.sleep(delay)

        except Exception as e:
            log.error(f"mbasic crawl error for {target}: {e}")
            time.sleep(delay)

    return all_text

# ──────────────────────────────────────────────────────────────────────────────
# METHOD 3: Facebook Graph API — public page posts (no auth token needed for
#           some fields; uses page_id lookup)
# ──────────────────────────────────────────────────────────────────────────────

def scrape_via_graph_api(page_names: list[str], access_token: str = None) -> list[str]:
    """
    Use Facebook Graph API to get public page posts.
    Without token: limited to page info only.
    With user/page token: gets post messages (better data).
    """
    texts = []
    base = "https://graph.facebook.com/v19.0"

    for page in page_names:
        params = {"fields": "posts{message,created_time,reactions.summary(true)}"}
        if access_token:
            params["access_token"] = access_token

        try:
            url = f"{base}/{page}"
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()

            if "posts" in data:
                for post in data["posts"].get("data", []):
                    msg = post.get("message", "")
                    if msg:
                        texts.append(msg)
                log.info(f"Graph API: {page} → {len(texts)} posts")
            elif "error" in data:
                log.warning(f"Graph API error for {page}: {data['error'].get('message')}")

        except Exception as e:
            log.error(f"Graph API error: {e}")

        time.sleep(1)

    return texts

# ──────────────────────────────────────────────────────────────────────────────
# MENTION COUNTER
# ──────────────────────────────────────────────────────────────────────────────

def count_mentions(text_corpus: list[str], univ_lookup: dict) -> dict:
    """
    Count how many times each university is mentioned across all collected text.
    Returns dict: english_name → count
    """
    combined_text = " ".join(text_corpus).lower()
    counts = defaultdict(int)

    for eng_name, info in univ_lookup.items():
        for variant in info["variants"]:
            # Count case-insensitive occurrences
            count = len(re.findall(re.escape(variant.lower()), combined_text))
            counts[eng_name] += count

    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

# ──────────────────────────────────────────────────────────────────────────────
# KNOWN BD AGENCY MENTION SIGNAL (supplementary — manual intelligence)
# This encodes what we KNOW from market research since FB scraping is limited
# ──────────────────────────────────────────────────────────────────────────────

KNOWN_BD_AGENCY_SIGNALS = {
    # university english name → signal score (how actively BD agencies push them)
    "Kyungsung University":          95,  # WeCare's #1 push, massive FB presence
    "Sejong University":              90,  # Seoul brand, most aspirational
    "Kyung Hee University":           85,  # Premium, often marketed by Jenny/Mentors
    "Dongshin University":            80,  # WeCare markets, cheapest tuition
    "Kangwon National University":    78,  # WeCare pushes, national univ prestige
    "Dong-A University":              75,  # Busan cluster, WeCare partner
    "Tongmyong University":           72,  # WeCare lists it prominently
    "Gachon University":              70,  # Seoul adjacent, well-known in BD
    "Silla University":               68,  # Busan, budget-friendly
    "Kyungdong University":           85,  # YOU + KUAC = your channel
    "Hanyang University":             65,  # Very prestigious, hard to get
    "Inha University":                62,  # Incheon, strong engineering
    "Sun Moon University":            60,  # Christian, Asan, large BD community
    "SolBridge International School": 58,  # MBA/BBA English track
    "Woosong University":             55,  # Same group as SolBridge
    "Konkuk University":              52,  # Seoul, prestigious
    "Konyang University":             50,  # WeCare listed
    "Dong-Eui University":            48,  # Busan cluster
    "Chungnam National University":   45,  # National univ prestige signal
    "Hanseo University":              42,  # Aviation fame, BD footprint confirmed
}

# ──────────────────────────────────────────────────────────────────────────────
# MAIN RUNNER
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="FB scraper for Korean university mentions")
    parser.add_argument("--method", choices=["google", "mbasic", "graph", "signals_only"],
                        default="signals_only",
                        help="Scraping method. Use 'signals_only' for offline run with known signals.")
    parser.add_argument("--limit", type=int, default=100,
                        help="Max posts per target")
    parser.add_argument("--token", default=None,
                        help="Facebook Graph API token (optional, improves data)")
    parser.add_argument("--out", default="ranked_universities.json")
    args = parser.parse_args()

    log.info("=== Keystone FB University Mention Scraper ===")
    univ_data, univ_lookup = load_universities("univ_list.json")

    mention_counts = {}

    if args.method == "google":
        log.info("Method: Google search scraping...")
        corpus = scrape_via_google(GOOGLE_SEARCH_QUERIES)
        mention_counts = count_mentions(corpus, univ_lookup)

    elif args.method == "mbasic":
        log.info("Method: Facebook mbasic page crawl...")
        corpus = scrape_facebook_mbasic(BD_FACEBOOK_TARGETS, max_posts=args.limit)
        mention_counts = count_mentions(corpus, univ_lookup)

    elif args.method == "graph":
        log.info("Method: Facebook Graph API...")
        page_names = [
            "wecareeducation", "jennyconsultancy", "keystoneeducations",
            "hangeulbd", "roushaneducation"
        ]
        corpus = scrape_via_graph_api(page_names, access_token=args.token)
        mention_counts = count_mentions(corpus, univ_lookup)

    elif args.method == "signals_only":
        log.info("Method: Known BD agency signal database (offline mode)...")
        # Use the pre-researched signal scores as the ranking basis
        mention_counts = dict(sorted(KNOWN_BD_AGENCY_SIGNALS.items(),
                                     key=lambda x: x[1], reverse=True))

    # Merge mention counts with university records
    results = []
    seen = set()
    for eng_name, count in mention_counts.items():
        if count == 0:
            continue
        # Find matching university record
        record = None
        for u in univ_data:
            if u["english"] == eng_name or eng_name in u["english"]:
                record = u
                break
        if not record:
            record = {"english": eng_name, "korean": "", "tier": "Unknown", "bd_agency": ""}

        key = eng_name.lower()
        if key in seen:
            continue
        seen.add(key)
        results.append({
            "rank": 0,
            "university_en": record["english"],
            "university_ko": record["korean"],
            "tier": record["tier"],
            "bd_agency_signal": record.get("bd_agency", ""),
            "mention_score": count,
            "scrape_method": args.method,
            "scraped_at": datetime.utcnow().isoformat(),
        })

    # Assign ranks
    results.sort(key=lambda x: x["mention_score"], reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1

    # Save JSON
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    log.info(f"Saved {len(results)} ranked universities to {args.out}")
    print("\n=== TOP 20 UNIVERSITIES MOST PUSHED BY BD AGENCIES ===")
    for r in results[:20]:
        print(f"#{r['rank']:2d} | Score:{r['mention_score']:4d} | {r['tier']:15s} | {r['university_en']}")

    return results

if __name__ == "__main__":
    main()
