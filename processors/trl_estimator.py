#!/usr/bin/env python3
# Dependencies: stdlib only
"""Estimate Technology Readiness Level (TRL 1-9) from collector items."""

from datetime import datetime, timezone

PHASE_TRL = {
    "early phase 1": 3,
    "phase 1": 4,
    "phase 2": 5,
    "phase 3": 6,
    "phase 4": 7,
}


def trl_from_clinical(extra: dict) -> tuple[int, str]:
    phase = (extra.get("phase") or "").lower()
    for label, trl in sorted(PHASE_TRL.items(), key=lambda x: -len(x[0])):
        if label in phase:
            return trl, f"clinical trial {extra.get('phase', '')}"
    if extra.get("status") == "RECRUITING":
        return 4, "recruiting trial (phase unknown)"
    return 4, "clinical trial"


def trl_from_collector(item: dict) -> tuple[int, str]:
    collector = item["collector"]
    extra = item.get("extra") or {}
    text = f"{item['title']} {item['summary']}".lower()

    if collector == "arxiv":
        if any(w in text for w in ("deploy", "production", "commercial")):
            return 6, "applied research paper"
        return 3, "academic preprint"

    if collector == "clinicaltrials":
        return trl_from_clinical(extra)

    if collector == "launch_library":
        status = (extra.get("status") or "").lower()
        if status in ("success", "complete"):
            return 9, "completed launch"
        return 8, "upcoming launch"

    if collector == "vc_news":
        if any(w in text for w in ("seed", "pre-seed")):
            return 4, "early-stage funding"
        if any(w in text for w in ("series", "growth", "ipo")):
            return 7, "growth-stage funding"
        return 5, "funding news"

    if collector == "rss":
        if any(w in text for w in ("approved", "clearance", "fda")):
            return 7, "regulatory milestone (RSS)"
        if any(w in text for w in ("pilot", "trial", "study")):
            return 5, "pilot or study (RSS)"
        if any(w in text for w in ("launch", "release", "available")):
            return 8, "product launch (RSS)"
        return 4, "industry news (RSS)"

    return 3, "default estimate"


def build_trl_payload(items: list[dict], warnings: list[str]) -> dict:
    entries = []
    by_industry: dict[str, list[int]] = {}

    for item in items:
        trl, rationale = trl_from_collector(item)
        entry = {
            "id": item.get("id") or "",
            "title": item["title"],
            "url": item["url"],
            "industry": item["industry"],
            "collector": item["collector"],
            "trl": trl,
            "rationale": rationale,
        }
        entries.append(entry)
        by_industry.setdefault(item["industry"], []).append(trl)

    industry_avg = {
        ind: round(sum(vals) / len(vals), 1)
        for ind, vals in by_industry.items()
        if vals
    }

    payload = {
        "source": "trl_estimator",
        "processed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": len(entries),
        "industry_avg_trl": industry_avg,
        "items": entries,
    }
    if warnings:
        payload["warnings"] = warnings
    return payload
