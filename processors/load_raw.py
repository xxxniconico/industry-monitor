#!/usr/bin/env python3
"""Load latest collector outputs from data/raw/."""

import json
from glob import glob
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

RAW_PATTERNS = [
    ("arxiv", "data/raw/feeds/arxiv_*.json"),
    ("rss", "data/raw/rss/*.json"),
    ("clinicaltrials", "data/raw/feeds/clinical_trials_*.json"),
    ("launch_library", "data/raw/feeds/launches_*.json"),
    ("vc_news", "data/raw/feeds/vc_news_*.json"),
]


def latest_file(pattern: str) -> Path | None:
    files = sorted(glob(str(ROOT / pattern)))
    return Path(files[-1]) if files else None


def normalize_item(collector: str, item: dict) -> dict | None:
    title = (item.get("title") or item.get("name") or "").strip()
    if not title:
        return None

    url = (item.get("url") or "").strip()
    published = (
        item.get("published")
        or item.get("launch_date")
        or item.get("start_date")
        or ""
    )
    summary = (item.get("summary") or "").strip()

    industry = item.get("industry")
    if not industry:
        if collector in ("clinicaltrials",):
            industry = "medical"
        elif collector in ("launch_library",):
            industry = "space"
        else:
            industry = "AI"

    return {
        "title": title,
        "url": url,
        "published": published,
        "industry": industry,
        "summary": summary,
        "collector": collector,
        "extra": {
            k: v
            for k, v in item.items()
            if k
            not in ("title", "name", "url", "published", "launch_date", "start_date", "summary", "industry")
        },
    }


def load_all_raw() -> tuple[list[dict], list[str]]:
    """Return (normalized items, warnings)."""
    items: list[dict] = []
    warnings: list[str] = []

    for collector, pattern in RAW_PATTERNS:
        path = latest_file(pattern)
        if path is None:
            warnings.append(f"missing: {pattern}")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            warnings.append(f"{path.name}: read error {exc}")
            continue
        if data.get("error"):
            warnings.append(f"{path.name}: {data['error']}")
        for raw in data.get("items") or []:
            norm = normalize_item(collector, raw)
            if norm:
                items.append(norm)

    return items, warnings
