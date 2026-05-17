#!/usr/bin/env python3
# Dependencies: requests, feedparser
"""Monitor RSS feeds across AI, medical, space, and drone industries."""

import json
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import feedparser
import requests

USER_AGENT = "IndustryMonitor/1.0 (contact: industry-monitor@local)"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "rss"

FEEDS = [
    {"name": "ArXiv CS.AI", "url": "http://export.arxiv.org/rss/cs.AI", "industry": "AI"},
    {"name": "Stanford HAI", "url": "https://hai.stanford.edu/rss.xml", "industry": "AI"},
    {
        "name": "MIT Technology Review",
        "url": "https://www.technologyreview.com/feed/",
        "industry": "AI",
    },
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "industry": "AI"},
    {"name": "STAT News", "url": "https://www.statnews.com/feed/", "industry": "medical"},
    {
        "name": "FDA News",
        "url": "https://www.fda.gov/about-fda/contact-fda/rss-feeds/fda-news-releases/rss.xml",
        "industry": "medical",
    },
    {
        "name": "FierceBiotech",
        "url": "https://www.fiercebiotech.com/rss.xml",
        "industry": "medical",
    },
    {"name": "SpaceNews", "url": "https://spacenews.com/feed/", "industry": "space"},
    {
        "name": "NASA Breaking News",
        "url": "https://www.nasa.gov/news-release/feed/",
        "industry": "space",
    },
    {"name": "DroneDJ", "url": "https://dronedj.com/feed/", "industry": "drone"},
]


def normalize_published(entry: dict) -> str:
    if entry.get("published_parsed"):
        try:
            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except (TypeError, ValueError):
            pass
    if entry.get("updated_parsed"):
        try:
            dt = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except (TypeError, ValueError):
            pass
    raw = entry.get("published") or entry.get("updated") or ""
    if raw:
        try:
            dt = parsedate_to_datetime(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except (TypeError, ValueError, OverflowError):
            return raw
    return ""


def fetch_feed(feed: dict) -> list[dict]:
    resp = requests.get(
        feed["url"],
        headers={"User-Agent": USER_AGENT},
        timeout=15,
    )
    resp.raise_for_status()
    parsed = feedparser.parse(resp.content)
    items = []
    for entry in parsed.entries:
        items.append(
            {
                "title": (entry.get("title") or "").strip(),
                "url": (entry.get("link") or "").strip(),
                "published": normalize_published(entry),
                "source_feed": feed["name"],
                "industry": feed["industry"],
                "summary": (entry.get("summary") or entry.get("description") or "").strip(),
            }
        )
    return items


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    result = {"source": "rss_monitor", "fetched_at": fetched_at, "items": []}
    errors = []

    for feed in FEEDS:
        try:
            result["items"].extend(fetch_feed(feed))
        except Exception as exc:
            errors.append({"feed": feed["name"], "error": str(exc)})

    if errors:
        result["errors"] = errors

    output_path = OUTPUT_DIR / f"{today}.json"
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(result['items'])} items to {output_path}")
    if errors:
        print(f"Warning: {len(errors)} feed(s) failed")


if __name__ == "__main__":
    main()
