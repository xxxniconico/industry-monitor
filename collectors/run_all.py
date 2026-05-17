#!/usr/bin/env python3
"""Run all collectors and print a summary. Usage: python collectors/run_all.py"""

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COLLECTORS = [
    "paper_tracker",
    "rss_monitor",
    "clinical_trials",
    "launch_tracker",
    "vc_tracker",
]


def run_collector(name: str) -> dict:
    path = Path(__file__).parent / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.main()
    return {"name": name, "status": "ok"}


def summarize_outputs() -> list[dict]:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    checks = [
        ROOT / "data" / "raw" / "feeds" / f"arxiv_{today}.json",
        ROOT / "data" / "raw" / "rss" / f"{today}.json",
        ROOT / "data" / "raw" / "feeds" / f"clinical_trials_{today}.json",
        ROOT / "data" / "raw" / "feeds" / f"launches_{today}.json",
        ROOT / "data" / "raw" / "feeds" / f"vc_news_{today}.json",
    ]
    rows = []
    for p in checks:
        row = {"file": str(p.relative_to(ROOT)), "exists": p.exists(), "items": 0, "error": None}
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            row["items"] = len(data.get("items") or [])
            row["error"] = data.get("error")
            row["errors"] = data.get("errors")
        rows.append(row)
    return rows


def main() -> int:
    log_path = ROOT / "data" / "raw" / "_run_all_log.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []

    for name in COLLECTORS:
        try:
            run_collector(name)
            lines.append(f"{name}: OK")
        except Exception as exc:
            lines.append(f"{name}: FAIL {exc}")

    lines.append("--- summary ---")
    for row in summarize_outputs():
        lines.append(
            f"{row['file']}: items={row['items']} error={row['error']!r} "
            f"feed_errors={len(row.get('errors') or [])}"
        )

    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    failed = sum(1 for row in summarize_outputs() if row["items"] == 0)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
