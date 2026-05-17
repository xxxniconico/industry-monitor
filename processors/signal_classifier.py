#!/usr/bin/env python3
# Dependencies: stdlib only
"""Classify raw items into seven industry signal types."""

import hashlib
from datetime import datetime, timezone

SIGNAL_TYPES = ["技术链", "资本", "技术", "监管", "市场", "人才", "基建"]

# (signal_type, keywords) — order matters for tie-break via position
RULES: list[tuple[str, list[str]]] = [
    ("资本", [
        "funding", "raised", "investment", "venture", "series a", "series b",
        "million", "billion", "ipo", "acquisition", "融资", "投资", "并购",
    ]),
    ("监管", [
        "fda", "regulation", "regulatory", "approval", "compliance", "policy",
        "ban", "license", "监管", "获批", "合规", "政策",
    ]),
    ("人才", [
        "hire", "hiring", "talent", "workforce", "ceo", "appoint", "resign",
        "layoff", "人才", "招聘", "任命",
    ]),
    ("基建", [
        "datacenter", "data center", "infrastructure", "facility", "fab",
        "launch pad", "spaceport", "基建", "基础设施", "数据中心",
    ]),
    ("技术链", [
        "supply chain", "semiconductor", "chip", "foundry", "upstream",
        "downstream", "产业链", "供应链", "晶圆", "代工",
    ]),
    ("市场", [
        "market", "revenue", "sales", "customer", "demand", "pricing",
        "market share", "市场", "营收", "客户",
    ]),
    ("技术", [
        "paper", "arxiv", "algorithm", "model", "breakthrough", "research",
        "prototype", "patent", "论文", "算法", "模型", "突破",
    ]),
]

COLLECTOR_DEFAULTS = {
    "arxiv": "技术",
    "clinicaltrials": "技术",
    "launch_library": "基建",
    "vc_news": "资本",
}


def item_id(item: dict) -> str:
    key = item.get("url") or f"{item['collector']}:{item['title']}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def classify_text(text: str, collector: str) -> tuple[str, float]:
    text_lower = text.lower()
    scores: dict[str, int] = {t: 0 for t in SIGNAL_TYPES}

    for signal_type, keywords in RULES:
        for kw in keywords:
            if kw in text_lower:
                scores[signal_type] += 1

    best_type = max(scores, key=lambda k: scores[k])
    best_score = scores[best_type]

    if best_score == 0:
        default = COLLECTOR_DEFAULTS.get(collector, "技术")
        return default, 0.35

    total = sum(scores.values())
    confidence = round(min(0.95, 0.4 + best_score / max(total, 1) * 0.5), 2)
    return best_type, confidence


def classify_item(item: dict) -> dict:
    blob = f"{item['title']} {item['summary']}"
    signal_type, confidence = classify_text(blob, item["collector"])
    return {
        "id": item_id(item),
        "title": item["title"],
        "url": item["url"],
        "published": item["published"],
        "industry": item["industry"],
        "signal_type": signal_type,
        "collector": item["collector"],
        "confidence": confidence,
    }


def build_signals_payload(items: list[dict], warnings: list[str]) -> dict:
    signals = [classify_item(i) for i in items]
    by_type = {t: 0 for t in SIGNAL_TYPES}
    by_industry: dict[str, int] = {}

    for s in signals:
        by_type[s["signal_type"]] = by_type.get(s["signal_type"], 0) + 1
        by_industry[s["industry"]] = by_industry.get(s["industry"], 0) + 1

    payload = {
        "source": "signal_classifier",
        "processed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": len(signals),
        "by_type": by_type,
        "by_industry": by_industry,
        "signals": signals,
    }
    if warnings:
        payload["warnings"] = warnings
    return payload


def build_events_payload(signals: list[dict]) -> dict:
    """Timeline of classified items, newest first."""
    dated = [s for s in signals if s.get("published")]
    undated = [s for s in signals if not s.get("published")]

    def sort_key(s: dict) -> str:
        return s.get("published") or ""

    dated.sort(key=sort_key, reverse=True)

    events = []
    for s in dated + undated:
        events.append(
            {
                "id": s["id"],
                "date": s.get("published") or "",
                "title": s["title"],
                "url": s["url"],
                "industry": s["industry"],
                "signal_type": s["signal_type"],
                "collector": s["collector"],
            }
        )

    return {
        "source": "events",
        "processed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": len(events),
        "events": events,
    }
