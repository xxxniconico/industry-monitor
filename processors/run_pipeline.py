#!/usr/bin/env python3
"""Run Phase 2 pipeline: raw JSON → processed signals / events / TRL."""
# Usage: python processors/run_pipeline.py

import json
import sys
from pathlib import Path

_PROCESSORS = Path(__file__).resolve().parent
if str(_PROCESSORS) not in sys.path:
    sys.path.insert(0, str(_PROCESSORS))

from load_raw import load_all_raw
from signal_classifier import build_events_payload, build_signals_payload
from trl_estimator import build_trl_payload

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "processed"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    items, warnings = load_all_raw()
    if not items:
        print("ERROR: no raw items loaded")
        for w in warnings:
            print(f"  {w}")
        return 1

    signals_payload = build_signals_payload(items, warnings)
    signals = signals_payload["signals"]

    # attach ids for TRL pass
    for item, sig in zip(items, signals):
        item["id"] = sig["id"]

    events_payload = build_events_payload(signals)
    trl_payload = build_trl_payload(items, warnings)

    paths = {
        "signals.json": signals_payload,
        "events.json": events_payload,
        "trl_tracker.json": trl_payload,
    }

    for name, data in paths.items():
        path = OUT_DIR / name
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {path.relative_to(ROOT)} ({data.get('total', len(data.get('signals', data.get('events', data.get('items', [])))))} records)")

    print("\nSignal breakdown:")
    for t, n in sorted(signals_payload["by_type"].items(), key=lambda x: -x[1]):
        print(f"  {t}: {n}")

    print("\nIndustry avg TRL:")
    for ind, avg in trl_payload.get("industry_avg_trl", {}).items():
        print(f"  {ind}: {avg}")

    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for w in warnings[:5]:
            print(f"  {w}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
