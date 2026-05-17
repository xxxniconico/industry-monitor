#!/usr/bin/env python3
# Dependencies: streamlit, pandas
"""Industry Monitor v5 — 依赖树 + 远期预测 :8505"""

import json
from pathlib import Path
from collections import Counter, defaultdict

import pandas as pd
import streamlit as st

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
.stApp { background: #1f1633; }
.conclusion { background:linear-gradient(135deg,#2a1f40,#1f1633); border:1px solid #c2ef4e; border-radius:12px; padding:20px; margin-bottom:12px; }
.conclusion h3 { color:#c2ef4e; margin:0 0 8px 0; }
.conclusion .body { color:#c8c8d0; font-size:14px; line-height:1.65; }
.ind-section { margin:20px 0; }
.ind-title { color:#c2ef4e; font-size:22px; font-weight:bold; margin-bottom:2px; border-bottom:1px solid #333355; padding-bottom:6px; }
.tree { font-family: 'Courier New', monospace; font-size:13px; color:#a0a0b0; line-height:1.8; margin:12px 0; padding:14px; background:#1f1830; border-radius:8px; border:1px solid #2a2540; }
.tree .root { color:#c2ef4e; font-weight:bold; }
.tree .primary { color:#ffffff; }
.tree .secondary { color:#a0a0b0; }
.tree .arrow { color:#666688; }
.tree .trl { font-size:11px; }
.chain-detail { background:#2a1f40; border-radius:8px; padding:12px 16px; margin:6px 0; border-left:4px solid; }
.chain-detail .cname { font-size:15px; font-weight:bold; }
.chain-detail .cmeta { font-size:11px; color:#8888a0; margin-top:2px; }
.chain-detail .ctrig { font-size:12px; color:#a0a0b0; margin-top:4px; }
.chain-detail .cdeps { font-size:11px; color:#8888a0; margin-top:3px; }
.chain-detail .cscore { font-size:26px; font-weight:bold; }
.prediction-hero { background:linear-gradient(135deg,#0d1b2a,#1a1030); border:1px solid #4ec2ef; border-radius:12px; padding:24px; margin:16px 0; }
.prediction-hero h3 { color:#4ec2ef; margin:0 0 4px 0; }
.prediction-hero .sub { color:#6a9ab5; font-size:13px; margin-bottom:16px; }
.prediction-card { background:#1a2a3a; border-radius:10px; padding:16px; margin:10px 0; border-left:3px solid #4ec2ef; }
.prediction-card .phase { color:#4ec2ef; font-size:12px; font-weight:bold; margin-bottom:4px; }
.prediction-card .event { color:#ffffff; font-size:14px; font-weight:bold; }
.prediction-card .timeline { color:#6a9ab5; font-size:12px; margin-top:4px; }
.prediction-card .cascade { color:#a0c0d0; font-size:12px; margin-top:6px; line-height:1.5; }
.prediction-card .impact { color:#c2ef4e; font-size:12px; margin-top:4px; font-weight:bold; }
.tier-badge { display:inline-block; padding:2px 8px; border-radius:8px; font-size:10px; font-weight:bold; margin-right:4px; }
hr.div { border-color:#333355; margin:18px 0; }
</style>""", unsafe_allow_html=True)


@st.cache_data(ttl=60)
def load_all():
    sp, cp = PROCESSED / "signals.json", MODELS / "tech_chains.json"
    if not sp.exists(): return None, None, None
    signals = json.loads(sp.read_text())
    chains = json.loads(cp.read_text()) if cp.exists() else {"chains":[]}
    return signals, chains, signals.get("processed_at","")


def score_chain(chain, items):
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
    signal_score = min(100, matches * 15)
    boost = min(30, cap * 5 + reg * 3 + infra * 4)
    trl = chain["trl"]
    if 5 <= trl <= 7: trl_score = 100
    elif 4 <= trl < 5 or 7 < trl <= 8: trl_score = 70
    elif trl < 4: trl_score = 30
    else: trl_score = 50
    urgency = 1.2 if chain.get("tier") == "short" else 1.0
    return min(100, max(5, int(((signal_score + boost) * 0.6 + trl_score * 0.4) * urgency))), matches, cap


def build_tree(chains, industry):
    """Build a dependency tree for an industry."""
    chain_map = {c["id"]: c for c in chains["chains"]}
    ind_chains = [c for c in chains["chains"] if c["industry"] == industry]
    
    # Find roots (chains with no dependencies, or only depends on chains outside industry)
    all_ids = {c["id"] for c in ind_chains}
    roots = [c for c in ind_chains if not any(d in all_ids for d in c.get("depends_on",[]))]
    # Also include chains that depend on roots from other industries
    non_roots = [c for c in ind_chains if c not in roots]
    
    lines = []
    
    def render_node(chain, prefix="", is_last=True):
        connector = "└── " if is_last else "├── "
        role_symbol = "◆" if chain["role"] == "primary" else "◇"
        t = TIER[chain["tier"]]
        bar = "█" * int(chain["trl"]) + "░" * (9 - int(chain["trl"]))
        lines.append(f'{prefix}{connector}<span class="primary">{role_symbol} {chain["name"]}</span> <span class="trl" style="color:{t["color"]}">TRL {chain["trl"]:.1f} [{bar}]</span>')
        
        # Show children
        children = [chain_map[d] for d in chain.get("drives",[]) if d in all_ids]
        for i, child in enumerate(children):
            child_prefix = prefix + ("    " if is_last else "│   ")
            render_node(child, child_prefix, i == len(children) - 1)
    
    for i, root in enumerate(roots):
        t = TIER[root["tier"]]
        bar = "█" * int(root["trl"]) + "░" * (9 - int(root["trl"]))
        tier_badge = f'<span style="color:{t["color"]}">[{t["label"]}]</span>'
        lines.append(f'<span class="root">◆ {root["name"]}</span> {tier_badge} <span class="trl" style="color:{t["color"]}">TRL {root["trl"]:.1f} [{bar}]</span>')
        
        children = [chain_map[d] for d in root.get("drives",[]) if d in all_ids]
        for j, child in enumerate(children):
            render_node(child, "", j == len(children) - 1)
        
        if i < len(roots) - 1:
            lines.append("")
    
    # Add chains that don't fit in the tree (depend on outside)
    for c in non_roots:
        if c not in roots and not any(c["id"] in chain_map[r].get("drives",[]) for r in roots):
            t = TIER[c["tier"]]
            bar = "█" * int(c["trl"]) + "░" * (9 - int(c["trl"]))
            ext_deps = [chain_map[d]["name"] for d in c.get("depends_on",[]) if d in chain_map and chain_map[d]["industry"] != industry]
            dep_note = f' <span class="arrow">(依赖: {", ".join(ext_deps)})</span>' if ext_deps else ""
            lines.append(f'<span class="root">◆ {c["name"]}</span> <span style="color:{t["color"]}">[{t["label"]}]</span> <span class="trl" style="color:{t["color"]}">TRL {c["trl"]:.1f} [{bar}]</span>{dep_note}')
    
    return "\n".join(lines)


def render_prediction_section(chains):
    """Dedicated prediction section with cascade analysis."""
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


def render_conclusion(chains, items):
    chain_map = {c["id"]: c for c in chains["chains"]}
    scored = [(c, *score_chain(c, items)) for c in chains["chains"]]
    scored.sort(key=lambda x: -x[2])
    
    short_top = [(c,s,m,cap) for c,s,m,cap in scored if c["tier"]=="short"][:2]
    long_preds = [c for c in chains["chains"] if c.get("prediction")]
    
    lines = [f"**{len(items)} 条信号。** "]
    
    if short_top:
        c, s, _, _ = short_top[0]
        lines.append(f"短期核心关注：<b>{c['name']}</b>（机会分 {s}），它是当前驱动下游链最多的主链。")
    
    if long_preds:
        lines.append(f"{len(long_preds)} 条远期链有明确预测路径，突破后将触发二级以上产业变革。")
    
    lines.append(f"\n<b>关键依赖链：</b>CoWoS 产能 → GPU 供给 → 光模块 / 液冷 / 铜连接。CoWoS 是当前 AI 硬件链的总阀门。")
    
    return "\n".join(lines)


def main():
    signals, chains, processed_at = load_all()
    
    st.markdown('<h1 style="color:#c2ef4e;margin-bottom:0;">📡 行业趋势监控</h1>', unsafe_allow_html=True)
    st.markdown(f'<span style="color:#8888a0;font-size:13px;">依赖树 · 三级分层 · 远期预测 ｜ {processed_at[:16] if processed_at else "—"}</span>', unsafe_allow_html=True)
    st.markdown('<hr class="div">', unsafe_allow_html=True)
    
    if not signals: st.warning("暂无数据"); return
    items = signals.get("signals", [])
    chain_map = {c["id"]: c for c in chains["chains"]}
    
    # ── CONCLUSION ──
    c = render_conclusion(chains, items)
    st.markdown(f'<div class="conclusion"><h3>📊 综合研判</h3><div class="body">{c}</div></div>', unsafe_allow_html=True)
    
    # ── INDUSTRY TREES ──
    for ind_key in ["AI", "medical", "space", "drone"]:
        st.markdown(f'<div class="ind-title">{IND[ind_key]}</div>', unsafe_allow_html=True)
        
        # Dependency tree
        tree = build_tree(chains, ind_key)
        if tree.strip():
            st.markdown(f'<div class="tree">{tree}</div>', unsafe_allow_html=True)
        
        # Chain details (expanded)
        ind_chains = [c for c in chains["chains"] if c["industry"] == ind_key]
        ind_chains.sort(key=lambda c: (0 if c["role"]=="primary" else 1, {"short":0,"medium":1,"long":2}[c["tier"]]))
        
        for c in ind_chains:
            score, matches, cap = score_chain(c, items)
            t = TIER[c["tier"]]
            pct = c["trl"] / 9
            is_primary = c["role"] == "primary"
            
            deps = [chain_map[d]["name"] for d in c.get("depends_on",[]) if d in chain_map]
            driven = [chain_map[d]["name"] for d in c.get("drives",[]) if d in chain_map]
            
            cols = st.columns([5, 0.6])
            with cols[0]:
                st.markdown(f"""
                <div class="chain-detail" style="border-left-color:{t['color']};">
                  <span class="tier-badge" style="background:{t['bg']};color:{t['color']};">{t['label']}</span>
                  <span class="cname" style="color:{t['color']};">{'◆' if is_primary else '◇'} {c['name']}</span>
                  <div class="cmeta">{c['chain']}</div>
                  <div style="display:flex;align-items:center;gap:6px;margin-top:4px;">
                    <span style="font-size:11px;color:#8888a0;">TRL {c['trl']:.1f}</span>
                    <div style="flex:1;height:5px;background:#333355;border-radius:3px;">
                      <div style="width:{pct*100}%;height:5px;background:{t['color']};border-radius:3px;"></div>
                    </div>
                  </div>
                  <div class="ctrig">🎯 {c['next_trigger']}</div>
                  {f'<div class="cdeps">↑ 依赖: {", ".join(deps)}</div>' if deps else ''}
                  {f'<div class="cdeps">↓ 驱动: {", ".join(driven)}</div>' if driven else ''}
                </div>
                """, unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f'<div class="cscore" style="color:{t["color"]};text-align:center;">{score}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="text-align:center;font-size:10px;color:#8888a0;">信{matches}·资{cap}</div>', unsafe_allow_html=True)
        
        st.markdown('<br>', unsafe_allow_html=True)
    
    st.markdown('<hr class="div">', unsafe_allow_html=True)
    
    # ── PREDICTION SECTION ──
    render_prediction_section(chains)
    
    st.markdown('<hr class="div">', unsafe_allow_html=True)
    st.caption("Hermes 行业趋势监控 v5 · 依赖树 · 预测驱动 · `python processors/run_pipeline.py` 刷新数据")


if __name__ == "__main__":
    main()
