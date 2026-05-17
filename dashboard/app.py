#!/usr/bin/env python3
# Dependencies: streamlit, pandas
"""Industry Monitor v5 — 依赖树 + 远期预测 :8505"""

import json
from pathlib import Path
from collections import Counter, defaultdict

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parent.parent
PROCESSED, MODELS = ROOT / "data" / "processed", ROOT / "data" / "models"

IND = {"AI": "🤖 AI", "medical": "🏥 医疗", "space": "🚀 航天", "drone": "🚁 低空"}
TIER = {
    "short":  {"label":"短期 0-12月","color":"#ef6060","bg":"#3a2020"},
    "medium": {"label":"中期 1-3年","color":"#efc24e","bg":"#3a3020"},
    "long":   {"label":"长期 3-10年","color":"#4ec2ef","bg":"#203040"}
}

st.set_page_config(page_title="行业趋势监控", page_icon="📡", layout="wide")
st.markdown("""<style>
/* ===== Sentry Design System — Industry Monitor ===== */
.stApp { background: #1f1633; font-family: 'Rubik', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif; color:#e5e7eb; }
/* Typography */
h1,h2,h3,h4,h5,h6 { font-family: 'Rubik',system-ui,sans-serif; letter-spacing:-0.01em; }
h1 { font-size:28px; font-weight:600; }
h3 { font-size:20px; font-weight:500; }
p,div,span,li { font-size:14px; line-height:1.55; }
/* Conclusion */
.conclusion {
  background:linear-gradient(135deg,#2a1f40,#1f1633);
  border:1px solid #c2ef4e; border-radius:12px; padding:24px; margin-bottom:16px;
  box-shadow:rgba(0,0,0,0.1) 0px 10px 15px -3px;
}
.conclusion h3 { color:#c2ef4e; margin:0 0 10px 0; font-size:18px; font-weight:600; }
.conclusion .body { color:#e5e7eb; font-size:15px; line-height:1.7; }
/* Industry title */
.ind-title { color:#c2ef4e; font-size:24px; font-weight:600; margin-bottom:4px; border-bottom:1px solid #362d59; padding-bottom:8px; letter-spacing:-0.02em; }
/* Tier badge */
.tier-badge { display:inline-block; padding:3px 10px; border-radius:8px; font-size:11px; font-weight:600; margin-right:6px; text-transform:uppercase; letter-spacing:0.3px; }
/* Divider */
hr.div { border-color:#362d59; margin:22px 0; }
/* ===== Causal Chain Card ===== */
.causal-card {
  background:#221b35; border-radius:14px; padding:24px 28px; margin:20px 0;
  border:1px solid #362d59;
  box-shadow:rgba(0,0,0,0.12) 0px 8px 20px -4px;
}
.causal-card h4 { color:#c2ef4e; margin:0 0 6px 0; font-size:18px; font-weight:600; letter-spacing:-0.01em; }
.causal-card .causal-tag { display:inline-block; padding:3px 10px; border-radius:6px; font-size:11px; margin-left:10px; text-transform:uppercase; letter-spacing:0.3px; }
.causal-card .causal-thesis { color:#a0a0b8; font-size:14px; line-height:1.6; margin:8px 0 16px 0; padding:12px 16px; background:#1a1530; border-radius:10px; border-left:3px solid #c2ef4e; }
/* Chain progress */
.chain-progress { height:4px; border-radius:4px; margin-bottom:16px; background:#2a2540; display:flex; overflow:hidden; }
.chain-progress .pg-trig { background:#4ecf4e; }
.chain-progress .pg-appr { background:#efc24e; }
.chain-progress .pg-pend { background:#3a3550; }
/* ===== Timeline Nodes ===== */
.causal-timeline { display:flex; gap:0; overflow-x:auto; padding:20px 0 12px; }
.causal-node { flex:0 0 180px; text-align:center; position:relative; padding:12px 6px 10px; border-radius:8px; }
.causal-node.trig-bg { background:rgba(78,207,78,0.06); }
.causal-node.appr-bg { background:rgba(239,194,78,0.05); }
.causal-node .n-dot { width:14px; height:14px; border-radius:50%; margin:0 auto 6px; }
.causal-node .n-dot.trig { background:#4ecf4e; box-shadow:0 0 12px rgba(78,207,78,0.5); }
.causal-node .n-dot.appr { background:#efc24e; box-shadow:0 0 8px rgba(239,194,78,0.4); }
.causal-node .n-dot.pend { background:#555577; }
.causal-node .n-time { font-size:11px; color:#8888a0; margin-bottom:4px; letter-spacing:0.02em; }
.causal-node .n-label { font-size:13px; color:#e5e7eb; line-height:1.35; font-weight:600; }
.causal-node .n-opp { font-size:10px; color:#c2ef4e; line-height:1.3; margin-top:4px; max-width:165px; }
/* Score bar */
.n-scorebar { height:3px; border-radius:3px; margin:5px auto 0; max-width:100px; background:#3a3550; }
.n-scorebar .fill { height:100%; border-radius:3px; }
/* Tech breakthroughs in node */
.causal-node .n-tech-divider { margin:7px 0 4px; border-top:1px solid #2a2540; position:relative; }
.causal-node .n-tech-divider span { font-size:9px; color:#8888a0; background:#221b35; padding:0 8px; position:relative; top:-8px; text-transform:uppercase; letter-spacing:0.5px; }
.causal-node .n-tech-item { font-size:10px; color:#a0a0d0; line-height:1.35; margin:3px 0; padding:4px 6px; background:#1a1530; border-radius:4px; border-left:2px solid #362d59; text-align:left; }
.causal-node .n-tech-item.breakthrough { border-left-color:#c2ef4e; }
.causal-node .n-tech-item .ti-tech { font-weight:600; }
.causal-node .n-tech-item .ti-impact { color:#7777a0; }
.causal-node .n-tech-item .ti-meta { font-size:9px; color:#5a5a7a; margin-top:2px; }
/* Investable themes in node */
.causal-node .n-invest-divider { margin:6px 0 3px; border-top:1px solid #2a2540; position:relative; }
.causal-node .n-invest-divider span { font-size:9px; color:#8888a0; background:#221b35; padding:0 8px; position:relative; top:-8px; text-transform:uppercase; letter-spacing:0.5px; }
.causal-node .n-invest-item { font-size:10px; color:#d0c080; line-height:1.3; margin:3px 0; padding:4px 6px; background:#1a1810; border-radius:4px; border-left:2px solid #5a5020; text-align:left; }
.causal-node .n-invest-item .ti-theme { font-weight:600; }
.causal-node .n-invest-item .ti-ticker { color:#9a9050; font-size:9px; }
.causal-node .n-invest-item .ti-tam { color:#7a7030; font-size:9px; margin-top:2px; }
/* Arrows */
.causal-arrow { flex:0 0 28px; display:flex; align-items:flex-start; justify-content:center; padding-top:12px; font-size:16px; font-weight:bold; }
/* Evidence (collapsed) */
.causal-evidence { background:#1a1530; border-radius:10px; padding:14px 18px; margin-top:14px; border:1px solid #2a2540; }
.causal-evidence .ev-title { color:#a0a0b8; font-size:13px; font-weight:600; }
.causal-evidence .ev-node { margin:6px 0; padding:8px 12px; border-radius:6px; border-left:3px solid #362d59; font-size:13px; color:#c8c8d0; line-height:1.5; }
.causal-evidence .ev-node.trig { border-left-color:#4ecf4e; background:#1a2a1a; color:#c0e0c0; }
.causal-evidence .ev-node.appr { border-left-color:#efc24e; background:#2a2a1a; color:#e0d0a0; }
.causal-evidence .ev-node .ev-label { font-weight:600; color:#e5e7eb; display:block; margin-bottom:3px; font-size:13px; }
.causal-evidence .ev-node .ev-desc { color:#a0a0b8; font-size:12px; }
/* Counter signals + alternative triggers */
.causal-meta { margin-top:8px; display:flex; gap:8px; flex-wrap:wrap; }
.causal-meta .meta-badge { font-size:10px; padding:4px 8px; border-radius:5px; line-height:1.3; max-width:280px; }
.causal-meta .meta-counter { background:#2a1515; border:1px solid #5a3030; color:#e0a0a0; }
.causal-meta .meta-counter::before { content:"⚠️ 反信号: "; color:#e06060; font-weight:600; }
.causal-meta .meta-alt { background:#151a2a; border:1px solid #30405a; color:#a0c0e0; }
.causal-meta .meta-alt::before { content:"🔄 备选路径: "; color:#6090d0; font-weight:600; }
/* Porter force badges */
.causal-node .n-porter { display:flex; flex-wrap:wrap; gap:2px; justify-content:center; margin-top:2px; }
.causal-node .n-porter .pf-badge { font-size:9px; padding:2px 5px; border-radius:3px; white-space:nowrap; }
.pf-accelerate { background:#1a2a1a; color:#8ecf8e; }
.pf-resist { background:#2a1a1a; color:#e0a0a0; }
.pf-feedback { background:#1a1a2a; color:#a0a0e0; }
/* Chain analysis block */
.chain-analysis { background:#191e30; border-radius:10px; padding:16px 20px; margin:12px 0 4px; border:1px solid #2a3050; }
.chain-analysis .ca-title { color:#c2ef4e; font-size:15px; font-weight:600; margin-bottom:10px; }
.chain-analysis .ca-section { color:#c8c8d0; font-size:13px; line-height:1.65; margin:8px 0; padding:4px 0; border-bottom:1px solid #222840; }
.chain-analysis .ca-section:last-child { border-bottom:none; }
/* Framework cards */
.framework-card { background:#221b35; border-radius:12px; padding:20px 24px; margin:12px 0; border:1px solid #362d59; box-shadow:rgba(0,0,0,0.08) 0px 4px 12px; }
.framework-card h4 { color:#c2ef4e; font-size:16px; font-weight:600; margin:0 0 6px 0; }
.framework-card .meta { color:#a0a0b8; font-size:13px; margin-bottom:8px; }
.framework-card .force { font-size:14px; margin:6px 0; }
/* Streamlit overrides */
.stMarkdown p { font-size:14px !important; }
.stCaption { font-size:12px !important; color:#8888a0 !important; }
details summary { cursor:pointer; outline:none; }
details summary::marker { color:#c2ef4e; }
</style>""", unsafe_allow_html=True)


@st.cache_data(ttl=60)
def load_all():
    sp = PROCESSED / "signals.json"; cp = MODELS / "tech_chains.json"
    scp = MODELS / "s_curve.json"; pp = MODELS / "porter.json"
    tp = PROCESSED / "trl_tracker.json"; ap = PROCESSED / "alerts.json"
    if not sp.exists(): return None, None, None, None, None, None, None
    signals = json.loads(sp.read_text())
    chains = json.loads(cp.read_text()) if cp.exists() else {"chains":[]}
    s_curve = json.loads(scp.read_text()) if scp.exists() else {}
    porter = json.loads(pp.read_text()) if pp.exists() else {}
    trl_tracker = json.loads(tp.read_text()) if tp.exists() else {}
    alerts = json.loads(ap.read_text()) if ap.exists() else {}
    return signals, chains, s_curve, porter, trl_tracker, alerts, signals.get("processed_at","")

@st.cache_data(ttl=60)
def load_causal_chains():
    p = MODELS / "causal_chains.json"
    if p.exists():
        return json.loads(p.read_text())
    return {"chains": []}


import math
from datetime import datetime, timezone

TYPE_WEIGHTS = {
    "技术链": 1.0,   # direct tech progress — gold standard
    "资本":   0.8,   # investment validates real progress
    "基建":   0.7,   # infrastructure = deployment signal
    "技术":   0.5,   # papers/breakthroughs (arXiv noisy)
    "监管":   0.4,   # regulatory milestones
    "人才":   0.3,   # talent moves (sparse)
    "市场":   0.1,   # market news — high volume, low signal
}
FRESHNESS_LAMBDA = 60  # days, half-life ≈ 42 days


def compute_node_score(node, items):
    """Score = Σ(confidence × type_weight × freshness) × keyword_bonus."""
    kw = node.get("trigger_keywords", [])
    if not kw:
        return 0.0, []
    now = datetime.now(timezone.utc)
    # Per-node decay lambda: fast (AI apps) = 30, normal = 60, slow (semiconductor mfg) = 90, structural = 120
    lamb = node.get("decay_lambda", 60)
    scored = []
    distinct_kw = set()
    for s in items:
        text = (s.get("title", "") + " " + s.get("summary", "")).lower()
        hit = [k for k in kw if k.lower() in text]
        if not hit:
            continue
        distinct_kw.update(hit)
        conf = s.get("confidence", 0.5)
        type_w = TYPE_WEIGHTS.get(s.get("signal_type", ""), 0.1)
        try:
            dt = datetime.fromisoformat(s["published"].replace("Z", "+00:00"))
            age_days = max(0, (now - dt).total_seconds() / 86400)
        except Exception:
            age_days = 365
        freshness = math.exp(-age_days / lamb)
        scored.append((s, conf * type_w * freshness, hit))
    if not scored:
        return 0.0, []
    kw_bonus = min(1.5, 1.0 + 0.1 * (len(distinct_kw) - 1))
    total = sum(ms for _, ms, _ in scored) * kw_bonus
    scored.sort(key=lambda x: -x[1])
    return total, [s for s, _, _ in scored[:5]]


def eval_node_status(node, items, parent_scores=None, child_scores=None):
    """Full scoring model → (status, score, evidence).
    
    Improvements over v1:
    - Continuous upstream factor (not hard 0.3/0.7 cutoffs)
    - Reverse inference: strong children → weak upstream boost
    """
    score, evidence = compute_node_score(node, items)
    # Upstream validation — continuous: 0.3 + 0.7*(min_parent/2.0), capped at 1.0
    upstream = 1.0
    if parent_scores:
        ps = parent_scores.get(node["id"], [])
        if ps:
            mp = min(ps)
            upstream = min(1.0, 0.3 + 0.7 * (mp / 2.0))
    # Reverse inference: if node has zero score but children are strong, infer upstream activity
    reverse_boost = 0.0
    if child_scores and score < 0.5:
        cs = child_scores.get(node["id"], [])
        if cs:
            avg_child = sum(cs) / len(cs)
            if avg_child > 1.0:
                reverse_boost = avg_child * 0.3  # boost up to ~0.9 for very strong children
    final = max(score, reverse_boost) * upstream
    if final >= 2.0:
        return "triggered", round(final, 2), evidence
    elif final >= 0.5:
        return "approaching", round(final, 2), evidence
    return "pending", round(final, 2), evidence


def render_causal_chains(causal_data, ind_key, items):
    """Render causal chains for one industry as domino timeline cards."""
    ind_chains = [c for c in causal_data.get("chains", []) if c.get("industry") == ind_key]
    if not ind_chains:
        return

    for chain in ind_chains:
        # Flatten nodes into timeline order (BFS from seed)
        nodes = chain.get("nodes", [])
        node_map = {n["id"]: n for n in nodes}
        seed_id = chain.get("seed_node")
        if not seed_id or seed_id not in node_map:
            continue

        # BFS traversal to build ordered node list
        visited = set()
        order = []
        queue = [seed_id]
        while queue:
            nid = queue.pop(0)
            if nid in visited:
                continue
            visited.add(nid)
            node = node_map.get(nid)
            if node:
                order.append(node)
                for child in node.get("children", []):
                    cid = child.get("node")
                    if cid and cid not in visited:
                        queue.append(cid)

        if not order:
            continue

        # Build reverse dependency map for upstream validation
        parent_map = {}  # node_id → [parent_node_ids]
        child_map = {}   # node_id → [child_node_ids]
        for node in order:
            for child in node.get("children", []):
                cid = child.get("node")
                if cid:
                    parent_map.setdefault(cid, []).append(node["id"])
                    child_map.setdefault(node["id"], []).append(cid)

        # First pass: score all nodes without upstream (to get raw scores)
        raw_scores = {}
        node_evidence = {}
        for node in order:
            score, evidence = compute_node_score(node, items)
            raw_scores[node["id"]] = score
            node_evidence[node["id"]] = evidence

        # Second pass: compute final status with upstream validation + reverse inference
        node_statuses = {}
        node_final_scores = {}
        for node in order:
            # Collect parent scores
            parent_scores_map = {}
            for pid in parent_map.get(node["id"], []):
                parent_scores_map.setdefault(node["id"], []).append(raw_scores.get(pid, 0))
            # Collect child scores (for reverse inference)
            child_scores_map = {}
            for cid in child_map.get(node["id"], []):
                child_scores_map.setdefault(node["id"], []).append(raw_scores.get(cid, 0))
            status, score, evidence = eval_node_status(node, items, parent_scores_map, child_scores_map)
            node_statuses[node["id"]] = status
            node_final_scores[node["id"]] = score

        chain_has_triggered = any(s == "triggered" for s in node_statuses.values())
        chain_has_approaching = any(s == "approaching" for s in node_statuses.values())
        overall_label = "🟢 已触发" if chain_has_triggered else ("🟡 逼近中" if chain_has_approaching else "⚪ 待触发")

        # Build timeline HTML
        html = f'<div class="causal-card"><h4>🔗 {chain["label"]} <span class="causal-tag" style="background:#2a2a1a;color:#c2ef4e;">{overall_label}</span></h4>'
        # Chain thesis
        thesis = chain.get("thesis", "")
        if thesis:
            html += f'<div class="causal-thesis">💡 {thesis}</div>'

        # Counter signals + alternative triggers (chain-level meta)
        meta_items = []
        for node in order:
            cs = node.get("counter_signal")
            if cs:
                meta_items.append(f'<span class="meta-badge meta-counter">{cs}</span>')
            at = node.get("alternative_triggers")
            if at:
                meta_items.append(f'<span class="meta-badge meta-alt">{at}</span>')
        if meta_items:
            html += '<div class="causal-meta">' + "".join(meta_items) + '</div>'

        # Compute chain-level stats (used by both analysis + progress bar)
        n_total = len(order)
        n_trig = sum(1 for s in node_statuses.values() if s == "triggered")
        n_appr = sum(1 for s in node_statuses.values() if s == "approaching")
        n_pend = n_total - n_trig - n_appr

        # ── Chain Analysis Block ──
        triggered_nodes = [(n, node_statuses[n["id"]], node_final_scores[n["id"]]) for n in order if node_statuses[n["id"]] == "triggered"]
        approaching_nodes = [(n, node_statuses[n["id"]], node_final_scores[n["id"]]) for n in order if node_statuses[n["id"]] == "approaching"]
        # Porter force summary
        all_forces = {}
        for n in order:
            for f in n.get("porter_forces", []):
                key = f"{f['direction']} {f['force']}"
                all_forces.setdefault(key, []).append(f.get("note",""))
        
        html += '<div class="chain-analysis">'
        html += '<div class="ca-title">📊 链分析</div>'
        
        # Position
        html += '<div class="ca-section">'
        html += f'<strong>📍 当前位置:</strong> {n_total}节点链，{n_trig}🟢触发 {n_appr}🟡逼近 {n_pend}⚪待触发 (完成度 {int((n_trig+n_appr*0.5)/n_total*100)}%)'
        if triggered_nodes:
            html += '<br><span style="color:#4ecf4e;">🟢 已触发: </span>' + " · ".join(f"T+{n.get('lag_months',0)}月 {n['label']}" for n,_,_ in triggered_nodes)
        if approaching_nodes:
            html += '<br><span style="color:#efc24e;">🟡 逼近中: </span>' + " · ".join(f"T+{n.get('lag_months',0)}月 {n['label']}" for n,_,_ in approaching_nodes)
        html += '</div>'
        
        # Porter forces
        if all_forces:
            html += '<div class="ca-section"><strong>📐 结构力场:</strong> '
            force_lines = []
            for key, notes in all_forces.items():
                dir_icon = {"↗":"🟢","↘":"🔴","↻":"🔵"}.get(key[0],"")
                force_lines.append(f'{dir_icon} {key} {"、".join(notes[:2])}'[:100])
            html += "<br>".join(force_lines)
            html += '</div>'
        
        # Risks
        risks = []
        for n in order:
            cs = n.get("counter_signal")
            if cs: risks.append(f"⚠️ {n['label'][:12]}: {cs}")
            at = n.get("alternative_triggers")
            if at: risks.append(f"🔄 {n['label'][:12]}: {at}")
        if risks:
            html += '<div class="ca-section"><strong>⚠️ 风险与备选:</strong> '
            html += "<br>".join(r[:120] for r in risks[:4])
            html += '</div>'
        
        # Investment highlights
        invest_highlights = []
        for n in order:
            themes = n.get("investable_themes", [])
            if themes:
                best = max(themes, key=lambda t: {"growth":3,"early":2,"emerging":1,"declining":0,"vision":0}.get(t.get("stage",""),0))
                invest_highlights.append(f"T+{n.get('lag_months',0)}月 → {best['theme']} ({best.get('tam','?')})")
        if invest_highlights:
            html += '<div class="ca-section"><strong>💰 投资主线:</strong> '
            html += " · ".join(invest_highlights[:5])
            html += '</div>'
        
        html += '</div>'

        # Chain progress bar
        pct_trig = n_trig / n_total * 100
        pct_appr = n_appr / n_total * 100
        pct_pend = n_pend / n_total * 100
        html += f'<div class="chain-progress">'
        if n_trig: html += f'<div class="pg-trig" style="width:{pct_trig}%"></div>'
        if n_appr: html += f'<div class="pg-appr" style="width:{pct_appr}%"></div>'
        if n_pend: html += f'<div class="pg-pend" style="width:{pct_pend}%"></div>'
        html += f'</div>'

        html += '<div class="causal-timeline">'

        for i, node in enumerate(order):
            nst = node_statuses.get(node["id"], "pending")
            nscore = node_final_scores.get(node["id"], 0)
            dot_cls = {"triggered": "trig", "approaching": "appr", "pending": "pend"}.get(nst, "pend")
            status_emoji = {"triggered": "🟢", "approaching": "🟡", "pending": "⚪"}.get(nst, "⚪")
            lag = node.get("lag_months", 0)
            opp = node.get("opportunity", "")
            node_bg = "trig-bg" if nst == "triggered" else ("appr-bg" if nst == "approaching" else "")

            # Score bar color + width
            score_pct = min(100, nscore / 5.0 * 100)
            if nscore >= 2.0:
                bar_color = "#4ecf4e"
            elif nscore >= 0.5:
                bar_color = "#efc24e"
            else:
                bar_color = "#555577"

            html += f'<div class="causal-node {node_bg}">'
            html += f'<div class="n-time">T+{lag}月</div>'
            html += f'<div class="n-dot {dot_cls}"></div>'
            html += f'<div class="n-label">{status_emoji} {node["label"]}</div>'
            if opp:
                short_opp = opp[:50] + ("…" if len(opp) > 50 else "")
                html += f'<div class="n-opp">🎯 {short_opp}</div>'
            html += f'<div class="n-scorebar"><div class="fill" style="width:{score_pct}%;background:{bar_color};"></div></div>'
            # Tech breakthroughs inline
            tbs = node.get("tech_breakthroughs", [])
            if tbs:
                html += '<div class="n-tech-divider"><span>技术突破</span></div>'
                for tb in tbs:
                    cls = "breakthrough" if "→" in tb.get("tech","") else ""
                    mat = tb.get("maturity", {})
                    html += f'<div class="n-tech-item {cls}">'
                    html += f'<span class="ti-tech">{tb["tech"]}</span> '
                    html += f'<span class="ti-impact">{tb["impact"]}</span>'
                    if mat.get("trl","—") != "—":
                        html += f'<div class="ti-meta">TRL{mat["trl"]} · {mat.get("market","")} · {mat.get("cagr","")} · {mat.get("deploy","")[:25]}</div>'
                    html += '</div>'
            # Investable themes
            themes = node.get("investable_themes", [])
            if themes:
                html += '<div class="n-invest-divider"><span>可投主题</span></div>'
                for th in themes:
                    html += '<div class="n-invest-item">'
                    html += f'<span class="ti-theme">{th["theme"]}</span> '
                    html += f'<span class="ti-ticker">{th["ticker"]}</span>'
                    tam = th.get("tam","—")
                    cagr = th.get("cagr","—")
                    stage = th.get("stage","—")
                    if tam != "—":
                        stage_emoji = {"emerging":"🌱","early":"🌿","growth":"🌳","declining":"🍂","vision":"🔮"}.get(stage,"")
                        html += f'<div class="ti-tam">{stage_emoji} {stage} · {tam} · {cagr}</div>'
                    html += '</div>'
            # Porter force badges
            pf = node.get("porter_forces", [])
            if pf:
                html += '<div class="n-porter">'
                for f in pf:
                    cls = "pf-accelerate" if f["direction"]=="↗" else ("pf-resist" if f["direction"]=="↘" else "pf-feedback")
                    html += f'<span class="pf-badge {cls}">{f["direction"]} {f["force"]}</span>'
                html += '</div>'
            html += '</div>'

            if i < len(order) - 1:
                # Arrow color based on downstream node status
                next_nst = node_statuses.get(order[i+1]["id"], "pending")
                if nst == "triggered" and next_nst in ("triggered", "approaching"):
                    arrow_color = "#4ecf4e"
                elif nst in ("triggered", "approaching") and next_nst in ("triggered", "approaching"):
                    arrow_color = "#efc24e"
                else:
                    arrow_color = "#555577"
                html += f'<div class="causal-arrow" style="color:{arrow_color};">→</div>'

        html += '</div>'

        # Evidence section — show nodes with any evidence
        evidence_nodes = [(nid, node_evidence.get(nid, []), node_statuses.get(nid, "pending"), node_final_scores.get(nid, 0))
                          for nid in [n["id"] for n in order] if node_evidence.get(nid)]
        if evidence_nodes:
            n_trig_ev = sum(1 for _, _, s, _ in evidence_nodes if s == "triggered")
            n_appr_ev = len(evidence_nodes) - n_trig_ev
            summary = f"{len(evidence_nodes)}个节点有信号证据"
            if n_trig_ev: summary += f"（{n_trig_ev}🟢触发 + {n_appr_ev}🟡逼近）"
            html += f'<details class="causal-evidence" style="cursor:pointer;">'
            html += f'<summary class="ev-title" style="color:#c2ef4e;font-size:11px;">📋 信号证据 <span style="color:#8888a0;font-weight:normal;">{summary}</span></summary>'
            html += '<div style="margin-top:8px;">'
            for nid, ev_items, nst, nscore in evidence_nodes:
                node = node_map.get(nid)
                if not node:
                    continue
                cls = "trig" if nst == "triggered" else "appr"
                status_text = "✅ 已触发" if nst == "triggered" else "🟡 逼近"
                raw_s = raw_scores.get(nid, 0)
                html += f'<div class="ev-node {cls}">'
                html += f'<span class="ev-label">T+{node.get("lag_months",0)}月 {node["label"]} <span style="font-weight:normal;color:#8888a0;">({status_text} · {len(ev_items)}条 · 原始{raw_s:.1f}→最终{nscore:.1f}分)</span></span>'
                html += f'<span class="ev-desc">{node.get("description","")}</span>'
                for ev in ev_items[:2]:
                    t = ev.get("title", "")[:80]
                    if t:
                        html += f'<br><span style="color:#666688;font-size:10px;">📰 {t}</span>'
                html += '</div>'
            html += '</div></details>'

        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)


def score_chain(chain, items, chain_map=None):
    """Score = structural importance (60%) + signal momentum (40%).
    Structural: TRL window, dependency role, tier urgency — stable day to day.
    Signal: keyword hits, capital/regulation/infra boost — varies with news cycle."""
    kw = chain.get("trigger_keywords", [])
    matches, cap, reg, infra = 0, 0, 0, 0
    for s in items:
        if s.get("industry") != chain["industry"]: continue
        text = (s.get("title","")+" "+s.get("summary","")).lower()
        if any(k.lower() in text for k in kw):
            matches += 1
            t = s.get("signal_type","")
            if t == "资本": cap += 1
            elif t == "监管": reg += 1
            elif t == "基建": infra += 1

    # ── 1. TRL 窗口价值 (0-35) ──
    trl = chain["trl"]
    if 5 <= trl <= 7:
        trl_score = 35    # golden window — about to break through
    elif 4 <= trl < 5:
        trl_score = 28    # early but approaching
    elif 7 < trl <= 8:
        trl_score = 25    # deployed but still evolving
    elif trl < 4:
        trl_score = 15    # too early for market signal
    else:  # trl > 8
        trl_score = 18    # mature, low uncertainty

    # ── 2. 结构重要性 (0-25) ──
    # Root chains (no internal deps) are the "valves" of the system
    is_root = chain["role"] == "primary" and not chain.get("depends_on")
    n_drives = len(chain.get("drives", []))
    # Cross-industry drivers get extra credit
    has_cross = chain_map and any(
        d in chain_map and chain_map[d]["industry"] != chain["industry"]
        for d in chain.get("drives", [])
    ) if chain_map else False
    
    if n_drives >= 4:
        struct_score = 25    # major hub — drives 4+ downstream chains
    elif n_drives >= 2:
        struct_score = 20    # significant hub
    elif is_root and n_drives >= 1:
        struct_score = 18    # root chain with some reach
    elif n_drives >= 1 or has_cross:
        struct_score = 14    # drives at least one chain
    elif chain["role"] == "primary":
        struct_score = 12    # independent primary chain
    else:
        struct_score = 8     # secondary/supporting chain

    # ── 3. 信号动量 (0-40) ──
    # Matches: log-scale to prevent a few hits from dominating
    import math
    match_score = min(25, max(0, int(8 * math.log(matches + 1))))
    # Capital/regulation/infra boost
    cap_score = min(15, cap * 5 + reg * 3 + infra * 4)
    signal_score = match_score + cap_score

    raw = trl_score + struct_score + signal_score
    return min(100, max(10, raw)), matches, cap


def render_tech_radar(chains, industry, items):
    """Tech Radar: concentric rings (tiers) x 4 quadrants (industries). Blips = chains."""
    import math
    chain_map = {c["id"]: c for c in chains["chains"]}
    ind_chains = [c for c in chains["chains"] if c["industry"] == industry]
    all_ids = {c["id"] for c in ind_chains}

    if not ind_chains:
        return

    # ── Ring radii ──
    ring = {"short": (0.15, 0.35), "medium": (0.40, 0.60), "long": (0.65, 0.85)}

    # ── Place blips ──
    # theta: spread chains evenly within their tier ring
    positions = {}
    for tier in ["short", "medium", "long"]:
        tier_chains = [c for c in ind_chains if c["tier"] == tier]
        n = len(tier_chains)
        if n == 0: continue
        r_inner, r_outer = ring[tier]
        for i, c in enumerate(tier_chains):
            # Spread theta evenly, slight random jitter removed for clarity
            theta = (i / n) * 2 * math.pi
            # r based on TRL: lower TRL = closer to inner, higher = closer to outer
            trl_norm = min(1, max(0, (c["trl"] - 1) / 8))
            r = r_inner + trl_norm * (r_outer - r_inner)
            positions[c["id"]] = (theta, r, c)

    # ── Build figure ──
    fig = go.Figure()

    # Draw rings
    for tier_name, (r_inner, r_outer) in ring.items():
        t = TIER[tier_name]
        # Outer ring
        theta_ring = [i * 0.01 for i in range(0, 629)]
        fig.add_trace(go.Scatterpolar(
            r=[r_outer] * len(theta_ring), theta=theta_ring,
            mode="lines", line=dict(color=t["color"], width=1, dash="dot"),
            hoverinfo="none", showlegend=False,
        ))
        # Ring label
        mid_r = (r_inner + r_outer) / 2
        fig.add_annotation(
            x=0, y=mid_r, text=t["label"], showarrow=False,
            font=dict(size=9, color=t["color"]), xref="paper", yref="paper",
            xanchor="right",
        )

    # Draw blips
    for c in ind_chains:
        if c["id"] not in positions: continue
        theta, r, _ = positions[c["id"]]
        s, m, _ = score_chain(c, items, chain_map)
        t = TIER[c["tier"]]
        is_bb = c.get("backbone", False)

        # TRL heat color
        trl_norm = min(1, max(0, c["trl"] / 9))
        trl_r = int(239 * (1 - trl_norm) + 78 * trl_norm)
        trl_g = int(96 * (1 - trl_norm) + 194 * trl_norm)
        trl_b = int(96 * (1 - trl_norm) + 239 * trl_norm)
        blip_color = f"rgba({trl_r},{trl_g},{trl_b},0.85)"

        size = max(12, min(32, s * 0.32))
        symbol = "diamond" if is_bb else "circle"

        fig.add_trace(go.Scatterpolar(
            r=[r], theta=[theta],
            mode="markers+text",
            marker=dict(size=size, color=blip_color, symbol=symbol,
                        line=dict(color="#ffffff" if is_bb else t["color"], width=1.5 if is_bb else 1)),
            text=[c["name"]],
            textposition="top center",
            textfont=dict(size=9, color="#d0d0d0"),
            hovertemplate=f"<b>{c['name']}</b><br>TRL {c['trl']:.1f} · {s}分 · {m}条<br>🎯 {c.get('next_trigger','')[:60]}<extra></extra>",
            hoverlabel=dict(bgcolor="#1f1633"),
            showlegend=False,
        ))

    # Draw dependency lines
    for c in ind_chains:
        if c["id"] not in positions: continue
        for dep_id in c.get("depends_on", []):
            if dep_id not in positions: continue
            t0, r0, _ = positions[dep_id]
            t1, r1, _ = positions[c["id"]]
            fig.add_trace(go.Scatterpolar(
                r=[r0, r1], theta=[t0, t1],
                mode="lines",
                line=dict(color="rgba(85,85,119,0.4)", width=1, dash="dot"),
                hoverinfo="none", showlegend=False,
            ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#1f1633",
        font=dict(color="#c8c8d0", size=10),
        height=500,
        margin=dict(l=20, r=20, t=30, b=20),
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 0.95],
                            gridcolor="#333355", tickfont=dict(size=1), showticklabels=False),
            angularaxis=dict(visible=True, gridcolor="#333355",
                             tickfont=dict(size=1), showticklabels=False),
            bgcolor="#1f1633",
        ),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── Legend ──
    st.caption("● 内环=短期 ● 中环=中期 ● 外环=长期  |  ◆ 主链  ○ 副链  |  🔴←TRL高  🟢←TRL低  |  点线=依赖关系")

    # ── Compact dependency ──
    html = '<div style="margin-top:6px;font-size:10px;">'
    backbone_flow = [c for c in ind_chains if c.get("backbone")]
    backbone_flow.sort(key=lambda c: len(c.get("depends_on", [])))
    flow_names = " → ".join(c["name"] for c in backbone_flow[:6])
    html += f'<b style="color:#c2ef4e;">主链流:</b> {flow_names}'
    side_chains = [c for c in ind_chains if not c.get("backbone")]
    if side_chains:
        html += '<br><b style="color:#8888a0;">副链:</b> '
        html += " · ".join(c["name"] for c in side_chains)
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_prediction_section(chains):
    preds = [c for c in chains["chains"] if c.get("prediction")]
    if not preds: return
    
    st.markdown('<div class="prediction-hero">', unsafe_allow_html=True)
    st.markdown('<h3>🔮 技术链远期预测</h3>', unsafe_allow_html=True)
    st.markdown('<div class="sub">当这些技术链突破关键节点时，将触发什么级别的产业变革</div>', unsafe_allow_html=True)
    
    for c in preds:
        t = TIER[c["tier"]]
        trl_gap = 7 - c["trl"]
        est_years = "1-3 年" if trl_gap < 2 else ("3-5 年" if trl_gap < 4 else "5-10 年")
        
        # Parse prediction into phases
        pred_text = c["prediction"]
        # Extract cascading effects
        parts = pred_text.split("→")
        
        # Determine cascade depth
        cascade_count = len(parts)
        
        st.markdown(f"""
        <div class="prediction-card">
          <div class="phase"><span class="tier-badge" style="background:{t['bg']};color:{t['color']};">{t['label']}</span> {IND.get(c['industry'],'')} · 当前 TRL {c['trl']:.1f} · 预计 {est_years} 内突破</div>
          <div class="event">🎯 触发条件：{c['next_trigger']}</div>
          <div class="timeline">⏱ 当前瓶颈：{c['bottleneck']}</div>
          <div class="cascade">
            <b>🌊 连锁反应：</b><br>
            {"<br>".join(f"&nbsp;&nbsp;{'→' if i>0 else '①'} {p.strip()}" for i,p in enumerate(parts))}
          </div>
          <div class="impact">📊 市场影响层级：{"一级" if cascade_count <= 2 else "二级" if cascade_count <= 4 else "三级"} · {c['market_impact']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_conclusion(chains, items, alerts, trl_tracker):
    """Dynamic conclusion from signal data + cross-signal alerts + chain scores."""
    chain_map = {c["id"]: c for c in chains["chains"]}
    scored = [(c, *score_chain(c, items, chain_map)) for c in chains["chains"]]
    scored.sort(key=lambda x: -x[2])
    
    # Top chains by tier
    short_chains = [(c,s,m,cap) for c,s,m,cap in scored if c["tier"]=="short"]
    medium_chains = [(c,s,m,cap) for c,s,m,cap in scored if c["tier"]=="medium"]
    long_preds = [c for c in chains["chains"] if c.get("prediction")]
    
    # Signal distribution
    by_type = Counter(s.get("signal_type","") for s in items)
    by_ind = Counter(s.get("industry","") for s in items)
    
    # Cross-signal confluence (from alerts)
    ind_alerts = {ia["industry"]: ia for ia in alerts.get("industry_alerts", [])}
    global_alerts = alerts.get("global_alerts", [])
    hot_chains = alerts.get("hot_chains", [])
    
    # Industry avg TRL
    ind_trl = trl_tracker.get("industry_avg_trl", {})
    
    lines = []
    
    # ── Header: signal volume ──
    lines.append(f"**{len(items)} 条信号。**")
    active_types = [t for t,c in by_type.most_common() if c > 0 and t != "市场"]
    if active_types:
        lines.append(f"活跃信号类型：{' · '.join(f'{t}({c})' for t,c in by_type.most_common() if t in active_types[:4])}。")
    
    # ── Cross-signal confluence ──
    if global_alerts:
        lines.append(f"🌐 **全局告警：**{'; '.join(global_alerts[:2])}。")
    
    # ── Industry resonance ──
    resonance_parts = []
    for ind_key, label in [("AI","AI"),("medical","医疗"),("space","航天"),("drone","低空")]:
        ia = ind_alerts.get(ind_key)
        if ia and ia.get("confluence_level","").startswith("🟢"):
            resonance_parts.append(f"{label}({ia['confluence_level']})")
    if resonance_parts:
        lines.append(f"📡 **行业共振：**{' · '.join(resonance_parts)}。")
    
    # ── Short-term focus ──
    if short_chains:
        c, s, m, cap = short_chains[0]
        lines.append(f"⚡ **短期核心：**<b>{c['name']}</b>（机会分 {s}），{'驱动 ' + str(len(c.get('drives',[]))) + ' 条下游链' if c.get('drives') else '独立链'}。")
        if c.get("next_trigger"):
            lines.append(f"&nbsp;&nbsp;&nbsp;→ 下一触发：{c['next_trigger'][:80]}。")
    
    # ── Medium-term watch ──
    if medium_chains:
        c, s, m, cap = medium_chains[0]
        lines.append(f"🔭 **中期布局：**<b>{c['name']}</b>（机会分 {s}），当前 TRL {c['trl']:.1f}。")
    
    # ── Long-term predictions ──
    if long_preds:
        lines.append(f"🔮 **远期预测：**{len(long_preds)} 条链有明确突破路径。")
    
    # ── Industry TRL snapshot ──
    trl_parts = [f"{IND.get(k,k)}({v:.1f})" for k,v in ind_trl.items() if k in IND]
    if trl_parts:
        lines.append(f"📐 **行业 TRL 均值：**{' · '.join(trl_parts)}。")
    
    # ── Dependency highlight ──
    primary_roots = [c for c in chains["chains"] if c["role"]=="primary" and not c.get("depends_on")]
    if primary_roots:
        root = primary_roots[0]
        driven = [chain_map[d]["name"] for d in root.get("drives",[]) if d in chain_map]
        if driven:
            lines.append(f"🔗 **主依赖链：**{root['name']} → {' → '.join(driven[:3])}。{root['name']} 是当前 {root['industry']} 硬件链的总阀门。")
    
    # ── Hot chains from alerts ──
    if hot_chains:
        hc = hot_chains[0]
        lines.append(f"🔥 **最热技术链：**{hc['name']}（{hc['matches']} 条信号命中）。")
    
    return "\n".join(lines)


def render_framework_cards(porter, s_curve, trl_tracker, alerts):
    """Detailed framework cards: S-curve + TRL + top forces with evidence."""
    intensity_order = {"极高": 5, "高": 4, "强": 4, "中": 3, "关键": 3, "低": 2}
    trend_badge = {"↑": ("#ef6060", "↗ 增强"), "↓": ("#4ec2ef", "↘ 减弱"), "→": ("#666688", "→ 稳定")}
    force_label = {
        "new_entrants": "新进入者", "supplier_power": "供应商力",
        "buyer_power": "买方力", "substitutes": "替代品",
        "rivalry": "竞争强度", "complements": "互补生态"
    }
    
    port = porter.get("industries", {})
    inds = s_curve.get("industries", {})
    trl = trl_tracker.get("industry_avg_trl", {})
    ind_alerts = {ia["industry"]: ia for ia in alerts.get("industry_alerts", [])}
    
    industries = [
        ("AI", "🤖 AI", "#ef6060"),
        ("medical", "🏥 医疗", "#4ec2ef"),
        ("space", "🚀 航天", "#c2ef4e"),
        ("drone", "🚁 低空", "#efc24e"),
    ]
    
    cols = st.columns(4)
    for i, (ind_key, label, color) in enumerate(industries):
        pf = port.get(ind_key, {})
        sc = inds.get(ind_key, {})
        phase = sc.get("label", "—")
        trigger = sc.get("next_phase_trigger", "")[:70]
        live_trl = trl.get(ind_key, None)
        
        # Confluence
        ia = ind_alerts.get(ind_key, {})
        confluence = ia.get("confluence_level", "⚪ 无数据")
        specials = ia.get("special_alerts", [])
        
        # Top forces: intensity 4+ or trend ↑
        forces_ranked = []
        for fk, fl in force_label.items():
            f = pf.get(fk, {})
            score = intensity_order.get(f.get("intensity", "低"), 1)
            trend = f.get("trend", "→")
            # Boost score for trending-up forces
            if trend == "↑": score += 0.5
            elif trend == "↓": score -= 0.3
            forces_ranked.append((score, fl, f, trend))
        forces_ranked.sort(key=lambda x: -x[0])
        
        top_forces = forces_ranked[:2]
        shifting = [(fl, f, t) for _, fl, f, t in forces_ranked if t in ("↑", "↓")]
        
        with cols[i]:
            # Card
            html = f'<div style="background:#251e38;border-radius:10px;padding:14px;border-top:3px solid {color};height:100%;">'
            
            # Header: label + phase + TRL
            trl_str = f" · TRL {live_trl:.1f}" if live_trl else ""
            html += f'<div style="font-size:15px;font-weight:bold;color:#c2ef4e;margin-bottom:6px;">{label}</div>'
            html += f'<div style="font-size:11px;color:#a0a0b0;margin-bottom:4px;">📍 {phase}{trl_str}</div>'
            
            # Confluence badge
            confluence_color = "#c2ef4e" if "🟢" in confluence else ("#efc24e" if "🟡" in confluence else "#8888a0")
            html += f'<div style="font-size:10px;color:{confluence_color};margin-bottom:6px;">信号共振: {confluence}</div>'
            
            # Top forces
            html += '<div style="margin:6px 0;border-top:1px solid #333355;padding-top:6px;">'
            html += '<span style="font-size:10px;color:#666688;text-transform:uppercase;">核心五力</span>'
            for _, fl, f, trend in top_forces:
                intensity = f.get("intensity", "—")
                evidence = f.get("evidence", "")[:80]
                tc, tl = trend_badge.get(trend, ("#666688", "→"))
                html += f'<div style="margin:4px 0;font-size:11px;">'
                html += f'<b style="color:#d0d0d0;">{fl}</b> '
                html += f'<span style="background:#1a2a3a;color:{color};padding:1px 5px;border-radius:3px;font-size:10px;">{intensity}</span> '
                html += f'<span style="color:{tc};font-size:10px;">{tl}</span>'
                html += f'<div style="font-size:9px;color:#666688;margin-top:1px;line-height:1.3;">{evidence}…</div>'
                html += '</div>'
            html += '</div>'
            
            # Shifts
            if shifting:
                html += '<div style="margin:4px 0;border-top:1px solid #333355;padding-top:4px;">'
                shift_str = " · ".join(
                    f'<span style="color:{"#ef6060" if t=="↑" else "#4ec2ef"};font-size:10px;">{tl} {fl}</span>'
                    for fl, f, t in shifting[:2]
                    for tc, tl in [trend_badge.get(t, ("#666688","→"))]
                )
                html += f'<span style="font-size:10px;color:#8888a0;">趋势变化: </span>{shift_str}'
                html += '</div>'
            
            # Next trigger
            if trigger:
                html += f'<div style="margin-top:6px;font-size:9px;color:#555577;">→ {trigger}…</div>'
            
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)


def render_porter_radar(porter, s_curve, trl_tracker):
    """Render Porter 5+1 Forces as 2x2 radar chart grid with S-curve phase."""
    intensity_map = {"极高": 5, "高": 4, "强": 4, "中": 3, "关键": 3, "低": 2}
    trend_arrow = {"↑": "↗", "↓": "↘", "→": "→"}
    
    force_labels = ["新进入者", "供应商力", "买方力", "替代品", "竞争强度", "互补生态"]
    force_keys = ["new_entrants", "supplier_power", "buyer_power", "substitutes", "rivalry", "complements"]
    
    industries = [
        ("AI", "🤖 AI", "#ef6060"),
        ("medical", "🏥 医疗", "#4ec2ef"),
        ("space", "🚀 航天", "#c2ef4e"),
        ("drone", "🚁 低空", "#efc24e"),
    ]
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[label for _, label, _ in industries],
        specs=[[{"type": "polar"}, {"type": "polar"}],
               [{"type": "polar"}, {"type": "polar"}]],
        horizontal_spacing=0.12, vertical_spacing=0.15,
    )
    
    port = porter.get("industries", {})
    inds = s_curve.get("industries", {})
    trl = trl_tracker.get("industry_avg_trl", {})
    
    for i, (ind_key, _, color) in enumerate(industries):
        pf = port.get(ind_key, {})
        sc = inds.get(ind_key, {})
        row = i // 2 + 1
        col = i % 2 + 1
        
        # Build values and trend hints
        values = []
        trend_hints = []
        for fk in force_keys:
            f = pf.get(fk, {})
            v = intensity_map.get(f.get("intensity", "低"), 1)
            t = f.get("trend", "→")
            values.append(v)
            trend_hints.append(f"{trend_arrow.get(t, t)}")
        
        # Color: convert #ef6060 → rgba(239,96,96,0.25)
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        fill_color = f"rgba({r},{g},{b},0.25)"
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=[f"{l} {t}" for l, t in zip(force_labels, trend_hints)],
            fill='toself',
            fillcolor=fill_color,
            marker=dict(color=color, size=6),
            line=dict(color=color, width=2),
            name=ind_key,
            hovertemplate='%{theta}: <b>%{r}</b>/5<extra></extra>',
        ), row=row, col=col)
        
        # S-curve phase + TRL in subtitle
        phase = sc.get("label", "—")
        live_trl = trl.get(ind_key, f"{sc.get('trl_estimate', '?')}")
        n_up = sum(1 for f in pf.values() if isinstance(f, dict) and f.get("trend") == "↑")
        
        # Update subplot title with phase info
        current_title = fig.layout.annotations[i].text
        fig.layout.annotations[i].text = (
            f"{current_title}<br>"
            f"<span style='font-size:10px;color:#8888a0'>"
            f"📍{phase} · TRL {live_trl:.1f} · ↑{n_up}/6"
            f"</span>"
        )
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#1f1633",
        plot_bgcolor="#1f1633",
        font=dict(color="#c8c8d0", size=11),
        height=650,
        margin=dict(l=20, r=20, t=60, b=20),
        showlegend=False,
    )
    
    fig.update_polars(
        radialaxis=dict(
            visible=True, range=[0, 5.5],
            gridcolor="#333355", tickfont=dict(size=9, color="#666688"),
            tickvals=[1, 2, 3, 4, 5],
            ticktext=["低", "较低", "中", "高", "极高"],
        ),
        angularaxis=dict(
            gridcolor="#333355", tickfont=dict(size=10, color="#a0a0b0"),
            rotation=90, direction="clockwise",
        ),
        bgcolor="#1f1633",
    )
    
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def main():
    signals, chains, s_curve, porter, trl_tracker, alerts, processed_at = load_all()
    causal_data = load_causal_chains()

    st.markdown('<h1 style="color:#c2ef4e;margin-bottom:0;">📡 行业趋势监控</h1>', unsafe_allow_html=True)
    st.markdown(f'<span style="color:#8888a0;font-size:13px;">因果逻辑链 · 多米诺推演 · 五力框架 ｜ {processed_at[:16] if processed_at else "—"}</span>', unsafe_allow_html=True)
    st.markdown('<hr class="div">', unsafe_allow_html=True)

    if not signals: st.warning("暂无数据"); return
    items = signals.get("signals", [])
    chain_map = {c["id"]: c for c in chains["chains"]}

    # ── CONCLUSION ──
    c = render_conclusion(chains, items, alerts, trl_tracker)
    st.markdown(f'<div class="conclusion"><h3>📊 综合研判</h3><div class="body">{c}</div></div>', unsafe_allow_html=True)

    # ── FRAMEWORK ANALYSIS ──
    if s_curve and porter:
        st.markdown('<h3 style="color:#c2ef4e;">📐 波特五力 · 框架分析</h3>', unsafe_allow_html=True)
        render_framework_cards(porter, s_curve, trl_tracker, alerts)

    # ── CAUSAL CHAINS ──
    st.markdown('<hr class="div">', unsafe_allow_html=True)
    for ind_key in ["AI", "medical", "space", "drone"]:
        st.markdown(f'<div class="ind-title">{IND[ind_key]}</div>', unsafe_allow_html=True)
        render_causal_chains(causal_data, ind_key, items)
        st.markdown('<br>', unsafe_allow_html=True)

    st.markdown('<hr class="div">', unsafe_allow_html=True)
    st.caption("Hermes 行业趋势监控 v12 · 因果逻辑链 · 动态结论 · 五力框架 · `daily_update.sh` 自动刷新")


if __name__ == "__main__":
    main()
