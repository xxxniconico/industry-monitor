#!/usr/bin/env python3
"""Verify collector JSON outputs. Run: python collectors/check_outputs.py"""

import json
from datetime import datetime, timezone
from glob import glob
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")


def latest(pattern: str) -> Path | None:
    files = sorted(glob(str(ROOT / pattern)))
    return Path(files[-1]) if files else None


def check_file(label: str, path: Path | None) -> None:
    if path is None or not path.exists():
        print(f"{label}: MISSING ({path})")
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("items") or []
    n = len(items) if isinstance(items, list) else 0
    err = data.get("error")
    extra = data.get("errors")
    print(f"{label}: {path.relative_to(ROOT)}")
    print(f"  items={n}  error={err!r}")
    if extra:
        print(f"  feed_errors={len(extra)}")
    if n:
        first = items[0]
        title = first.get("title") or first.get("name") or first.get("nct_id") or "?"
        print(f"  first: {str(title)[:70]}")


def main() -> None:
    checks = [
        ("arxiv", latest(f"data/raw/feeds/arxiv_*.json") or ROOT / f"data/raw/feeds/arxiv_{TODAY}.json"),
        ("rss", latest(f"data/raw/rss/*.json") or ROOT / f"data/raw/rss/{TODAY}.json"),
        (
            "clinical_trials",
            latest(f"data/raw/feeds/clinical_trials_*.json")
            or ROOT / f"data/raw/feeds/clinical_trials_{TODAY}.json",
        ),
        ("launches", latest(f"data/raw/feeds/launches_*.json") or ROOT / f"data/raw/feeds/launches_{TODAY}.json"),
        ("vc_news", latest(f"data/raw/feeds/vc_news_*.json") or ROOT / f"data/raw/feeds/vc_news_{TODAY}.json"),
    ]
    print(f"date={TODAY}\n")
    for label, path in checks:
        check_file(label, path if isinstance(path, Path) else None)
        print()


if __name__ == "__main__":
    main()
