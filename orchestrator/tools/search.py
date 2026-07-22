"""Read-only web fetch for the scraper/content agents (competitor pages, etc.).

Read-only by construction: only GET, no auth, short timeout. Used for public
B2B/competitor pages — never for scraping student PII or Facebook profiles
(that's a hard guardrail from marketing/README.md).
"""
from __future__ import annotations

import urllib.request


def fetch(url: str, timeout: int = 20) -> str:
    if not url.startswith(("http://", "https://")):
        raise ValueError("only http(s) GET is allowed")
    req = urllib.request.Request(url, method="GET",
                                 headers={"User-Agent": "KeystoneResearch/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read(500_000).decode("utf-8", "ignore")  # cap size
