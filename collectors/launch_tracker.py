#!/usr/bin/env python3
# Dependencies: requests
"""Fetch upcoming space launches from The Space Devs Launch Library API."""

import json
from datetime import datetime, timezone
from pathlib import Path

import requests

API_URL = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=20"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "feeds"


def normalize_date(value: str) -> str:
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return value


def parse_launch(launch: dict) -> dict:
    rocket = launch.get("rocket") or {}
    configuration = rocket.get("configuration") or {}
    provider = launch.get("launch_service_provider") or {}
    mission = launch.get("mission") or {}

    return {
        "name": launch.get("name") or "",
        "provider": provider.get("name") or "",
        "rocket": configuration.get("full_name") or configuration.get("name") or "",
        "launch_date": normalize_date(launch.get("net") or ""),
        "status": launch.get("status", {}).get("name", "upcoming").lower(),
        "url": launch.get("url") or launch.get("slug") or "",
        "mission_type": mission.get("type") or "",
    }


def fetch_launches() -> dict:
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result = {"source": "launch_library", "fetched_at": fetched_at, "items": []}

    try:
        resp = requests.get(API_URL, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
    except requests.RequestException as exc:
        result["error"] = str(exc)
        return result
    except json.JSONDecodeError as exc:
        result["error"] = f"JSON parse error: {exc}"
        return result

    for launch in payload.get("results") or []:
        result["items"].append(parse_launch(launch))

    return result


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output_path = OUTPUT_DIR / f"launches_{today}.json"

    data = fetch_launches()
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(data.get('items', []))} items to {output_path}")
    if "error" in data:
        print(f"Warning: {data['error']}")


if __name__ == "__main__":
    main()
