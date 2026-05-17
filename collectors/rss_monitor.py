#!/usr/bin/env python3
# Dependencies: requests, feedparser
"""Monitor RSS feeds across AI, medical, space, and drone industries."""

import json
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import feedparser
import requests

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "rss"

FEEDS = [
    {"name": "ArXiv CS.AI", "url": "http://export.arxiv.org/rss/cs.AI", "industry": "AI"},
    {"name": "Stanford HAI", "url": "https://hai.stanford.edu/rss.xml", "industry": "AI"},
    {"name": "MIT Technology Review", "url": "https://www.technologyreview.com/feed/", "industry": "AI"},
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "industry": "AI"},
    {"name": "STAT News", "url": "https://www.statnews.com/feed/", "industry": "medical"},
    {"name": "WHO News", "url": "https://www.who.int/rss-feeds/news-english.xml", "industry": "medical"},
    {"name": "FiercePharma", "url": "https://www.fiercepharma.com/rss.xml", "industry": "medical"},
    {"name": "FierceBiotech", "url": "https://www.fiercebiotech.com/rss.xml", "industry": "medical"},
    # === Phase B 医疗扩源 (2026-05-17) ===
    {"name": "Nature Biotechnology", "url": "https://www.nature.com/nbt.rss", "industry": "medical"},
    {"name": "Nature Medicine", "url": "https://www.nature.com/nm.rss", "industry": "medical"},
    {"name": "Cell", "url": "https://www.cell.com/cell/current.rss", "industry": "medical"},
    {"name": "GEN News", "url": "https://www.genengnews.com/feed/", "industry": "medical"},
    {"name": "BioPharma Dive", "url": "https://www.biopharmadive.com/feeds/news/", "industry": "medical"},
    {"name": "Endpoints News", "url": "https://endpts.com/feed/", "industry": "medical"},
    {"name": "MobiHealthNews", "url": "https://www.mobihealthnews.com/rss.xml", "industry": "medical"},
    {"name": "The Medical Futurist", "url": "https://medicalfuturist.com/feed/", "industry": "medical"},
    {"name": "SpaceNews", "url": "https://spacenews.com/feed/", "industry": "space"},
    {"name": "NASA Breaking News", "url": "https://www.nasa.gov/news-release/feed/", "industry": "space"},
    {"name": "DroneDJ", "url": "https://dronedj.com/feed/", "industry": "drone"},
    # === Phase A 扩源 (2026-05-17) ===
    {"name": "Semiconductor Engineering", "url": "https://semiengineering.com/feed/", "industry": "AI"},
    {"name": "The Next Platform", "url": "https://www.nextplatform.com/feed/", "industry": "AI"},
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "industry": "AI"},
    {"name": "sUAS News", "url": "https://www.suasnews.com/feed/", "industry": "drone"},
    {"name": "DroneXL", "url": "https://dronexl.co/feed/", "industry": "drone"},
    {"name": "Space.com", "url": "https://www.space.com/feeds/all", "industry": "space"},
    {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index", "industry": "AI"},
    # === Phase C 半导体/AI硬件扩源 (2026-05-17) ===
    {"name": "Tom's Hardware", "url": "https://www.tomshardware.com/feeds/all", "industry": "AI"},
    {"name": "Semiconductor Digest", "url": "https://www.semiconductor-digest.com/feed/", "industry": "AI"},
    {"name": "EE Times", "url": "https://www.eetimes.com/feed/", "industry": "AI"},
    {"name": "ServeTheHome", "url": "https://www.servethehome.com/feed/", "industry": "AI"},
    {"name": "LightReading", "url": "https://www.lightreading.com/rss.xml", "industry": "AI"},
    # 量子计算
    {"name": "The Quantum Insider", "url": "https://thequantuminsider.com/feed/", "industry": "AI"},
    {"name": "Inside Quantum Technology", "url": "https://www.insidequantumtechnology.com/feed/", "industry": "AI"},
    # 制药工业
    {"name": "Pharmaceutical Technology", "url": "https://www.pharmaceutical-technology.com/feed/", "industry": "medical"},
    # 固态电池/eVTOL
    {"name": "Electrive", "url": "https://www.electrive.com/feed/", "industry": "drone"},
    {"name": "Aviation Week", "url": "https://aviationweek.com/rss.xml", "industry": "drone"},
    # === Phase D 韩国半导体 (2026-05-17) ===
    {"name": "SK Hynix Newsroom", "url": "https://news.skhynix.com/feed/", "industry": "AI"},
    {"name": "BusinessKorea", "url": "https://www.businesskorea.co.kr/rss/allArticle.xml", "industry": "AI"},
    {"name": "The Korea Times Tech", "url": "https://www.koreatimes.co.kr/www/rss/tech.xml", "industry": "AI"},
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
    resp = requests.get(feed["url"], headers={"User-Agent": USER_AGENT}, timeout=15)
    resp.raise_for_status()
    parsed = feedparser.parse(resp.content)
    items = []
    for entry in parsed.entries:
        items.append({
            "title": (entry.get("title") or "").strip(),
            "url": (entry.get("link") or "").strip(),
            "published": normalize_published(entry),
            "source_feed": feed["name"],
            "industry": feed["industry"],
            "summary": (entry.get("summary") or entry.get("description") or "").strip(),
        })
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
