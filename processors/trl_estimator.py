#!/usr/bin/env python3
# Dependencies: stdlib only
"""Estimate Technology Readiness Level (TRL 1-9). Uses tech_chains.json for domain-aware TRL."""

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAINS_PATH = ROOT / "data" / "models" / "tech_chains.json"

# Clinical trial phase → TRL
PHASE_TRL = {"early phase 1": 3, "phase 1": 4, "phase 2": 5, "phase 3": 6, "phase 4": 7}

# RSS feed → base TRL
RSS_TRL = {
    "ArXiv CS.AI": 3, "Stanford HAI": 5, "MIT Technology Review": 6,
    "OpenAI Blog": 7, "STAT News": 5, "WHO News": 5,
    "FierceBiotech": 5, "FiercePharma": 5, "SpaceNews": 5,
    "NASA Breaking News": 6, "DroneDJ": 5,
}

# Product/launch keywords → TRL boost
PRODUCT_KW = ["launch", "release", "announce", "unveil", "available", "shipping", "发布", "推出", "上市"]
CLINICAL_KW = ["trial", "study", "clinical", "phase", "临床", "试验"]
PILOT_KW = ["pilot", "demonstration", "demo", "prototype", "试点", "演示"]
APPROVAL_KW = ["approve", "clearance", "certify", "authorize", "获批", "认证", "许可"]


def load_chain_keywords() -> list[tuple[str, int, str]]:
    """Load (keyword, TRL, industry) tuples from tech_chains.json."""
    if not CHAINS_PATH.exists():
        return []
    chains = json.loads(CHAINS_PATH.read_text()).get("chains", [])
    results = []
    for c in chains:
        trl = int(c["trl"])
        for kw in c.get("trigger_keywords", []):
            results.append((kw.lower(), trl, c["industry"]))
    return sorted(results, key=lambda x: -len(x[0]))


def trl_from_clinical(extra: dict) -> tuple[int, str]:
    phase = (extra.get("phase") or "").lower()
    for label, trl in sorted(PHASE_TRL.items(), key=lambda x: -len(x[0])):
        if label in phase:
            return trl, f"clinical {extra.get('phase','')}"
    if extra.get("status") == "RECRUITING":
        return 4, "recruiting (phase unknown)"
    return 4, "clinical trial"


def trl_from_collector(item: dict, chain_kws: list) -> tuple[int, str]:
    collector = item.get("collector", "")
    text = f"{item.get('title','')} {item.get('summary','')}".lower()
    industry = item.get("industry", "")
    
    # Check tech_chains.json for domain-specific TRL
    for kw, trl, kw_ind in chain_kws:
        if kw in text and (kw_ind == industry or kw_ind == "AI"):
            return trl, f"chain keyword '{kw}'"
    
    if collector == "arxiv":
        if any(w in text for w in PRODUCT_KW):
            return 6, "applied research with deployment"
        if any(w in text for w in ["benchmark", "state-of-the-art", "SOTA"]):
            return 5, "benchmark-level research"
        return 3, "academic preprint"
    
    if collector == "clinicaltrials":
        return trl_from_clinical(item.get("extra", {}))
    
    if collector == "launch_library":
        status = (item.get("extra", {}).get("status") or "").lower()
        return 9 if status in ("success", "complete") else 8, "launch event"
    
    if collector == "vc_news":
        if any(w in text for w in ["seed", "pre-seed"]):
            return 4, "seed funding"
        if any(w in text for w in ["series c", "series d", "growth", "ipo"]):
            return 7, "late-stage funding"
        return 5, "venture funding"
    
    if collector == "rss":
        feed = item.get("source_feed", "")
        base = RSS_TRL.get(feed, 4)
        
        if any(w in text for w in APPROVAL_KW):
            return max(base + 2, 7), "regulatory approval"
        if any(w in text for w in PRODUCT_KW):
            return max(base + 1, 6), "product launch"
        if any(w in text for w in CLINICAL_KW):
            return max(base, 5), "clinical/research update"
        if any(w in text for w in PILOT_KW):
            return max(base, 5), "pilot/demonstration"
        return base, f"news from {feed}"
    
    return 3, "default"


def build_trl_payload(items: list[dict], warnings: list[str]) -> dict:
    chain_kws = load_chain_keywords()
    entries = []
    by_industry: dict[str, list[int]] = {}
    
    for item in items:
        trl, rationale = trl_from_collector(item, chain_kws)
        entry = {
            "id": item.get("id", ""),
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "industry": item.get("industry", ""),
            "collector": item.get("collector", ""),
            "trl": trl,
            "rationale": rationale,
        }
        entries.append(entry)
        by_industry.setdefault(item.get("industry", ""), []).append(trl)
    
    industry_avg = {
        ind: round(sum(vals) / len(vals), 1)
        for ind, vals in by_industry.items() if vals
    }
    
    return {
        "source": "trl_estimator",
        "processed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": len(entries),
        "industry_avg_trl": industry_avg,
        "items": entries,
        "warnings": warnings if warnings else [],
    }
