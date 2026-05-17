#!/usr/bin/env python3
# Dependencies: stdlib only
"""Classify raw items into seven industry signal types."""

import hashlib
import re
from datetime import datetime, timezone

SIGNAL_TYPES = ["技术链", "资本", "技术", "监管", "市场", "人才", "基建"]

# Source-based primary classification
SOURCE_SIGNAL = {
    "arxiv": "技术",
    "clinicaltrials": "技术",
    "launch_library": "市场",
    "vc_news": "资本",
}

# RSS feed → signal type mapping
RSS_FEED_SIGNAL = {
    "ArXiv CS.AI": "技术",
    "Stanford HAI": "市场",
    "MIT Technology Review": "市场",
    "OpenAI Blog": "市场",
    "STAT News": "市场",
    "WHO News": "监管",
    "FierceBiotech": "市场",
    "FiercePharma": "市场",
    "SpaceNews": "市场",
    "NASA Breaking News": "市场",
    "DroneDJ": "市场",
}

# Strong keyword overrides — only high-precision matches
CAPITAL_KW = [
    "raised $", "funding round", "series a", "series b", "series c",
    "closed $", "valuation", "ipo", "acquires", "acquisition",
    "融资", "亿元", "估值", "IPO", "上市",
]
REGULATION_KW = [
    "fda approved", "fda clearance", "fda clears", "regulatory approval",
    "banned", "sanction", "export control", "获批", "监管", "政策收紧",
]
INFRA_KW = [
    "datacenter", "data center", "factory", "manufacturing plant",
    "fabrication", "launch complex", "spaceport", "ground station",
    "数据中心", "工厂", "发射场",
]
TALENT_KW = [
    "appointed ceo", "hires", "hiring", "layoff", "layoffs", "resigns",
    "任命", "离职", "裁员",
]
TECH_CHAIN_KW = [
    "supply chain", "chip shortage", "shortage", "bottleneck",
    "供应链", "产能不足", "供不应求",
]

def item_id(item: dict) -> str:
    key = item.get("url") or f"{item.get('collector','')}:{item.get('title','')}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def classify_item(item: dict) -> dict:
    """Classify signal type. Source-based primary, keyword for refinement."""
    collector = item.get("collector", "")
    text = f"{item.get('title','')} {item.get('summary','')}"
    text_lower = text.lower()
    
    # Step 1: source-based default
    feed_name = item.get("source_feed", "")
    
    if collector == "rss" and feed_name in RSS_FEED_SIGNAL:
        signal_type = RSS_FEED_SIGNAL[feed_name]
        base_confidence = 0.55
    elif collector in SOURCE_SIGNAL:
        signal_type = SOURCE_SIGNAL[collector]
        base_confidence = 0.65
    else:
        signal_type = "技术"
        base_confidence = 0.40
    
    # Step 2: keyword overrides (only for non-RSS, or very strong RSS signals)
    override = None
    override_conf = 0
    
    if collector != "rss":
        # ArXiv/clinical/vc/launch — use keyword overrides
        if any(kw.lower() in text_lower for kw in CAPITAL_KW):
            override, override_conf = "资本", 0.80
        elif any(kw.lower() in text_lower for kw in REGULATION_KW):
            override, override_conf = "监管", 0.80
        elif any(kw.lower() in text_lower for kw in INFRA_KW):
            override, override_conf = "基建", 0.75
        elif any(kw.lower() in text_lower for kw in TALENT_KW):
            override, override_conf = "人才", 0.75
        elif any(kw.lower() in text_lower for kw in TECH_CHAIN_KW):
            override, override_conf = "技术链", 0.70
    else:
        # RSS — feed name is authoritative; only override for capital
        if any(kw.lower() in text_lower for kw in ["raised $", "funding round", "series a", "series b", "series c", "closed $", "ipo", "acquisition", "并购"]):
            override, override_conf = "资本", 0.85
    
    if override and override_conf > base_confidence + 0.10:
        signal_type = override
        confidence = override_conf
    else:
        confidence = base_confidence
    
    # Clinical trials special handling
    if collector == "clinicaltrials":
        extra = item.get("extra", {})
        phase = (extra.get("phase") or "").lower()
        if "phase 3" in phase:
            signal_type = "市场"
            confidence = 0.85
        elif "phase 2" in phase:
            signal_type = "技术"
            confidence = 0.75
    
    return {
        "id": item_id(item),
        "title": item["title"],
        "url": item.get("url", ""),
        "published": item.get("published", ""),
        "industry": item.get("industry", ""),
        "signal_type": signal_type,
        "collector": collector,
        "confidence": round(confidence, 2),
    }


def classify_all(items: list[dict]) -> list[dict]:
    return [classify_item(i) for i in items]


def build_signals_payload(items: list[dict], warnings: list[str]) -> dict:
    signals = classify_all(items)
    by_type = {t: 0 for t in SIGNAL_TYPES}
    by_industry = {}

    for s in signals:
        by_type[s["signal_type"]] = by_type.get(s["signal_type"], 0) + 1
        by_industry[s["industry"]] = by_industry.get(s["industry"], 0) + 1

    return {
        "source": "signal_classifier",
        "processed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": len(signals),
        "by_type": by_type,
        "by_industry": by_industry,
        "signals": signals,
        "warnings": warnings if warnings else [],
    }


def build_events_payload(signals: list[dict]) -> dict:
    dated = [s for s in signals if s.get("published")]
    dated.sort(key=lambda s: s.get("published", ""), reverse=True)
    undated = [s for s in signals if not s.get("published")]

    events = []
    for s in dated + undated:
        events.append({
            "id": s["id"], "date": s.get("published", ""),
            "title": s["title"], "url": s.get("url", ""),
            "industry": s["industry"], "signal_type": s["signal_type"],
            "collector": s["collector"],
        })

    return {
        "source": "events",
        "processed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": len(events),
        "events": events,
    }
