#!/usr/bin/env python3
# Dependencies: stdlib only
"""Cross-signal confluence engine. Detects multi-signal convergence and generates alerts."""

import json
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
MODELS = ROOT / "data" / "models"

SIGNAL_TYPES = ["技术链", "资本", "技术", "监管", "市场", "人才", "基建"]
SIGNAL_WEIGHTS = {"技术链": 20, "资本": 15, "技术": 20, "监管": 15, "市场": 10, "人才": 10, "基建": 10}

# Confluence thresholds: [signal_type] must have >= N items to be "active"
THRESHOLDS = {"资本": 5, "监管": 5, "基建": 3, "技术链": 3, "人才": 3, "技术": 20, "市场": 10}


def load_data():
    sp = PROCESSED / "signals.json"
    cp = MODELS / "tech_chains.json"
    scp = MODELS / "s_curve.json"
    if not sp.exists(): return None, None, None
    signals = json.loads(sp.read_text())
    chains = json.loads(cp.read_text()) if cp.exists() else {"chains": []}
    s_curve = json.loads(scp.read_text()) if scp.exists() else {}
    return signals, chains, s_curve


def analyze_industry(signals_list, chains, s_curve):
    """Analyze cross-signal confluence for each industry."""
    alerts = []
    items = signals_list.get("signals", [])
    
    for ind in ["AI", "medical", "space", "drone"]:
        ind_items = [s for s in items if s.get("industry") == ind]
        if not ind_items:
            continue
        
        # Count signals
        tc = Counter(s.get("signal_type") for s in ind_items)
        active = [t for t in SIGNAL_TYPES if tc.get(t, 0) >= THRESHOLDS.get(t, 999)]
        
        # Composite score
        total = len(ind_items)
        weighted = sum(tc.get(t, 0) * SIGNAL_WEIGHTS.get(t, 0) / 100 for t in SIGNAL_TYPES)
        
        # Industry S-curve
        sc = s_curve.get("industries", {}).get(ind, {})
        phase = sc.get("label", "—")
        
        # Confluence level
        n_active = len(active)
        if n_active >= 3:
            level = "🟢 强共振"
            detail = f"{n_active} 类信号同时活跃: {', '.join(active)}"
        elif n_active == 2:
            level = "🟡 双信号"
            detail = f"{', '.join(active)} 两类信号活跃"
        elif n_active == 1:
            level = "🔵 单信号"
            detail = f"仅 {active[0]} 活跃"
        else:
            level = "⚪ 信号稀疏"
            detail = "无信号类型达到阈值"
        
        # Special confluence checks
        specials = []
        cap = tc.get("资本", 0)
        tech_chain = tc.get("技术链", 0)
        reg = tc.get("监管", 0)
        infra = tc.get("基建", 0)
        
        if cap >= 5 and tech_chain >= 3:
            specials.append("💰+🧬 资本与技术链共振 → 拐点临近")
        if reg >= 5 and cap >= 5:
            specials.append("📋+💰 监管放松伴随资本涌入 → 政策窗口打开")
        if cap >= 5 and infra >= 3:
            specials.append("💰+🏗️ 资本和基建同步扩张 → 进入实质部署期")
        if tc.get("技术", 0) >= 30 and cap >= 5:
            specials.append("🔬+💰 技术突破吸引资本 → 创新加速期")
        
        # Top chains in this industry
        ind_chains = [c for c in chains["chains"] if c["industry"] == ind]
        top_chains = []
        for c in ind_chains:
            kw = c.get("trigger_keywords", [])
            matches = sum(1 for s in ind_items if any(k.lower() in (s.get("title","")+" "+s.get("summary","")).lower() for k in kw))
            if matches >= 2:
                top_chains.append({"name": c["name"], "matches": matches, "trl": c["trl"], "next_trigger": c["next_trigger"][:60]})
        top_chains.sort(key=lambda x: -x["matches"])
        
        alerts.append({
            "industry": ind,
            "total_signals": total,
            "active_signals": active,
            "confluence_level": level,
            "confluence_detail": detail,
            "weighted_score": round(weighted, 1),
            "s_curve_phase": phase,
            "special_alerts": specials,
            "top_chains": top_chains[:3],
            "signal_counts": dict(tc.most_common()),
        })
    
    return alerts


def generate_alerts_payload(signals_list, chains, s_curve):
    ind_alerts = analyze_industry(signals_list, chains, s_curve)
    
    # Global alerts
    global_alerts = []
    items = signals_list.get("signals", [])
    
    # Cross-industry capital surge
    cap_total = sum(1 for s in items if s.get("signal_type") == "资本")
    if cap_total >= 50:
        global_alerts.append(f"💰 全行业资本信号 {cap_total} 条，处于历史活跃水平")
    
    # Regulation density
    reg_total = sum(1 for s in items if s.get("signal_type") == "监管")
    if reg_total >= 20:
        global_alerts.append(f"📋 监管信号密集 ({reg_total}条)，多行业政策窗口可能同时打开")
    
    # Hot chains across industries
    all_chains = []
    for c in chains["chains"]:
        kw = c.get("trigger_keywords", [])
        ind_items = [s for s in items if s.get("industry") == c["industry"]]
        matches = sum(1 for s in ind_items if any(k.lower() in (s.get("title","")+" "+s.get("summary","")).lower() for k in kw))
        if matches >= 3:
            all_chains.append({"name": c["name"], "industry": c["industry"], "matches": matches, "trl": c["trl"]})
    all_chains.sort(key=lambda x: -x["matches"])
    
    return {
        "source": "cross_signal_engine",
        "processed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "global_alerts": global_alerts,
        "hot_chains": all_chains[:5],
        "industry_alerts": ind_alerts,
    }


def main():
    signals, chains, s_curve = load_data()
    if not signals:
        print("No signals data")
        return
    
    payload = generate_alerts_payload(signals, chains, s_curve)
    out = PROCESSED / "alerts.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"Wrote {out}")
    
    # Summary
    for ia in payload["industry_alerts"]:
        print(f"  {ia['industry']}: {ia['confluence_level']} ({ia['total_signals']} signals, {len(ia['active_signals'])} active)")
    if payload["global_alerts"]:
        for ga in payload["global_alerts"]:
            print(f"  🌐 {ga}")
    if payload["hot_chains"]:
        hc = payload["hot_chains"][0]
        print(f"  🔥 Hottest chain: {hc['name']} ({hc['matches']} matches)")


if __name__ == "__main__":
    main()
