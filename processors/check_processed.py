#!/usr/bin/env python3
"""Verify processed outputs. Run: python processors/check_processed.py"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"

FILES = {
    "signals.json": "signals",
    "events.json": "events",
    "trl_tracker.json": "items",
}


def main() -> None:
    for fname, key in FILES.items():
        path = PROCESSED / fname
        if not path.exists():
            print(f"{fname}: MISSING")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data.get(key) or []
        print(f"{fname}: {len(items)} records  processed_at={data.get('processed_at')}")
        if fname == "signals.json":
            print(f"  by_type: {data.get('by_type')}")
        if fname == "trl_tracker.json":
            print(f"  industry_avg_trl: {data.get('industry_avg_trl')}")


if __name__ == "__main__":
    main()
