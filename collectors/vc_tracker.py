#!/usr/bin/env python3
# Dependencies: requests, feedparser
"""Fetch VC/funding news from TechCrunch RSS."""

import json
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import feedparser
import requests

RSS_URL = "https://techcrunch.com/feed/"
USER_AGENT = "IndustryMonitor/1.0 (contact: industry-monitor@local)"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "feeds"

INDUSTRY_KEYWORDS = {
    "AI": [
        "ai", "artificial intelligence", "machine learning", "llm", "openai",
        "anthropic", "deep learning", "neural",
    ],
    "medical": [
        "biotech", "pharma", "health", "medical", "drug", "clinical", "fda",
        "therapeutic", "genomics",
    ],
    "space": [
        "space", "rocket", "satellite", "nasa", "spacex", "orbit", "launch",
    ],
    "drone": ["drone", "uav", "evtol", "air taxi", "autonomous flight"],
}


def infer_industry(title: str, summary: str) -> str:
    text = f"{title} {summary}".lower()
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return industry
    return "AI"


def normalize_published(entry: dict) -> str:
    if entry.get("published_parsed"):
        try:
            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
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


def parse_funding(summary: str) -> tuple[str | None, str | None]:
    amount_match = re.search(
        r"\$[\d,.]+\s*(?:million|billion|M|B|bn|m)?",
        summary,
        re.IGNORECASE,
    )
    funding_amount = amount_match.group(0) if amount_match else None

    company_match = re.search(
        r"([A-Z][A-Za-z0-9&.\- ]{1,40}?)\s+(?:raised|raises|secures|closed|announces)",
        summary,
    )
    company_name = company_match.group(1).strip() if company_match else None
    return funding_amount, company_name


def fetch_vc_news() -> dict:
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result = {"source": "vc_news", "fetched_at": fetched_at, "items": []}

    try:
        resp = requests.get(
            RSS_URL,
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        resp.raise_for_status()
        parsed = feedparser.parse(resp.content)
    except requests.RequestException as exc:
        result["error"] = str(exc)
        return result

    for entry in parsed.entries:
        title = (entry.get("title") or "").strip()
        summary = (entry.get("summary") or entry.get("description") or "").strip()
        funding_amount, company_name = parse_funding(f"{title}. {summary}")

        result["items"].append(
            {
                "title": title,
                "url": (entry.get("link") or "").strip(),
                "published": normalize_published(entry),
                "industry": infer_industry(title, summary),
                "summary": summary,
                "funding_amount": funding_amount,
                "company_name": company_name,
            }
        )

    return result


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output_path = OUTPUT_DIR / f"vc_news_{today}.json"

    data = fetch_vc_news()
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(data.get('items', []))} items to {output_path}")
    if "error" in data:
        print(f"Warning: {data['error']}")


if __name__ == "__main__":
    main()
