#!/usr/bin/env python3
# Dependencies: streamlit, pandas
"""Industry Monitor v2 — 技术链驱动的行业机会看板 :8505"""

import json
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
MODELS = ROOT / "data" / "models"

IND = {"AI": "🤖 AI", "medical": "🏥 医疗", "space": "🚀 航天", "drone": "🚁 低空"}
S_CURVE = {"AI": "早期大众·增长期", "medical": "早期采纳→大众", "space": "早期采纳·扩张", "drone": "创新者→采纳"}
SIG_EMOJI = {"技术链": "🧬", "资本": "💰", "技术": "🔬", "监管": "📋", "市场": "📊", "人才": "👥", "基建": "🏗️"}
CHAIN_COLORS = {"AI": "#c2ef4e", "medical": "#4ec2ef", "space": "#ef8f4e", "drone": "#ef4ec2"}

# ── Theme ──
st.set_page_config(page_title="行业趋势监控", page_icon="📡", layout="wide")
st.markdown(f"""<style>
.stApp {{ background: #1f1633; }}
.conclusion {{ background:linear-gradient(135deg,#2a1f40,#1f1633); border:1px solid #c2ef4e; border-radius:12px; padding:24px; margin-bottom:16px; }}
.conclusion h2 {{ color:#c2ef4e; margin:0 0 8px 0; }}
.conclusion p {{ color:#c8c8d0; font-size:14px; line-height:1.65; }}
.chain-card {{ background:#2a1f40; border-radius:8px; padding:14px; margin:6px 0; }}
.chain-card .name {{ color:#c2ef4e; font-weight:bold; font-size:14px; }}
.chain-card .trig {{ color:#f0a060; font-size:12px; margin-top:4px; }}
.bottleneck {{ background:#332040; border-left:3px solid #ef8f4e; padding:8px 12px; border-radius:4px; margin:6px 0; font-size:13px; color:#d0c0a0; }}
.opp-card {{ background:#2a1f40; border-radius:8px; padding:16px; text-align:center; }}
.opp-card .score {{ font-size:36px; font-weight:bold; }}
.opp-card .label {{ color:#8888a0; font-size:12px; }}
.alert-box {{ background:#332020; border-left:3px solid #ef6060; padding:10px 14px; border-radius:4px; margin:6px 0; }}
.alert-box .title {{ color:#ef6060; font-weight:bold; }}
.alert-box .body {{ color:#c8a0a0; font-size:13px; }}
hr.divider {{ border-color:#333355; margin:20px 0; }}
</style>""", unsafe_allow_html=True)


@st.cache_data(ttl=60)
def load_all():
    sp = PROCESSED / "signals.json"
    tp = PROCESSED / "trl_tracker.json"
    cp = MODELS / "tech_chains.json"
    if not sp.exists():
        return None, None, None, None
    signals = json.loads(sp.read_text())
    trl_data = json.loads(tp.read_text()) if tp.exists() else {}
    chains = json.loads(cp.read_text()) if cp.exists() else {"chains": []}
    return signals, trl_data, chains, signals.get("processed_at", "")


def compute_opportunity_score(chain, signals_list):
    """Score = signal_intensity × TRL_impact × trigger_proximity"""
    kw = chain.get("trigger_keywords", [])
    items = [s for s in signals_list if s.get("industry") == chain["industry"]]
    
    # Signal intensity: how many items match keywords
    matches = 0
    capital_hits = 0
    for s in items:
        text = (s.get("title", "") + " " + s.get("summary", "")).lower()
        if any(k.lower() in text for k in kw):
            matches += 1
            if s.get("signal_type") == "资本":
                capital_hits += 1
    
    # Normalize to 0-100
    signal_score = min(100, matches * 15)
    capital_bonus = min(20, capital_hits * 5)
    
    # TRL impact: chains at TRL 5-7 have highest opportunity (not too early, not too late)
    trl = chain["trl"]
    if 5 <= trl <= 7:
        trl_score = 100
    elif 4 <= trl < 5 or 7 < trl <= 8:
        trl_score = 70
    elif trl < 4:
        trl_score = 30
    else:
        trl_score = 50
    
    total = int((signal_score + capital_bonus) * 0.6 + trl_score * 0.4)
    return min(100, max(5, total)), matches, capital_hits


def render_conclusion(signals, chains, items):
    """Natural language conclusion with chain-specific insights."""
    tc = Counter(s.get("signal_type") for s in items)
    ic = Counter(s.get("industry") for s in items)
    
    # Find hottest chains
    chain_scores = []
    for c in chains["chains"]:
        score, matches, cap = compute_opportunity_score(c, items)
        chain_scores.append((c, score, matches))
    chain_scores.sort(key=lambda x: -x[1])
    hot = chain_scores[:3]
    
    parts = [
        f"**今日采集 {len(items)} 条信号。** 资本({tc.get('资本',0)})与技术({tc.get('技术',0)})信号活跃，监管信号{tc.get('监管',0)}条。",
        "",
        "### 🔥 最值得关注的技术链",
    ]
    for c, score, matches in hot:
        trl_bar = "█" * int(c["trl"]) + "░" * (9 - int(c["trl"]))
        parts.append(f"- **{c['name']}** ({IND.get(c['industry'],'')}) — TRL {c['trl']:.1f} `{trl_bar}` — 信号匹配 {matches} 条 · 机会分 {score}")
    
    # Bottleneck alerts
    stuck = [c for c in chains["chains"] if c["trl"] < 7 and c["trl"] >= 5]
    if stuck:
        parts.append("")
        parts.append("### ⚠️ 卡在关键节点的技术链")
        for c in stuck[:3]:
            parts.append(f"- **{c['name']}**: {c['bottleneck']}")
    
    return "\n".join(parts)


def render_chain_progress(chains, items):
    """Visual progress bars for each technology chain."""
    ind_order = ["AI", "medical", "space", "drone"]
    
    for ind in ind_order:
        ind_chains = [c for c in chains["chains"] if c["industry"] == ind]
        if not ind_chains:
            continue
            
        st.markdown(f"#### {IND[ind]}")
        
        for c in ind_chains:
            score, matches, cap_hits = compute_opportunity_score(c, items)
            trl = c["trl"]
            
            # TRL progress bar
            pct = trl / 9
            color = CHAIN_COLORS.get(ind, "#c2ef4e")
            
            cols = st.columns([3, 1])
            with cols[0]:
                st.markdown(f"""
                <div class="chain-card">
                  <div class="name">{c['name']}</div>
                  <div style="display:flex;align-items:center;gap:8px;margin-top:6px;">
                    <span style="color:#8888a0;font-size:12px;width:50px;">TRL {trl:.1f}</span>
                    <div style="flex:1;height:8px;background:#333355;border-radius:4px;">
                      <div style="width:{pct*100}%;height:8px;background:{color};border-radius:4px;"></div>
                    </div>
                    <span style="color:#8888a0;font-size:11px;">{c['chain']}</span>
                  </div>
                  <div class="trig">🎯 下一跳: {c['next_trigger']}</div>
                </div>
                """, unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f"""
                <div class="opp-card">
                  <div class="score" style="color:{color}">{score}</div>
                  <div class="label">机会分</div>
                  <div style="font-size:11px;color:#8888a0;">信号 {matches} · 资本 {cap_hits}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Bottleneck if stuck
            if 5 <= trl < 7:
                st.markdown(f'<div class="bottleneck">⚠️ 瓶颈: {c["bottleneck"]}</div>', unsafe_allow_html=True)


def render_opportunity_matrix(chains, items):
    """2D matrix: TRL (x) × Signal Intensity (y), bubble = market potential."""
    rows = []
    for c in chains["chains"]:
        score, matches, cap = compute_opportunity_score(c, items)
        rows.append({
            "技术链": c["name"],
            "行业": IND.get(c["industry"], c["industry"]),
            "TRL": c["trl"],
            "信号强度": score,
            "资本匹配": cap,
            "下一跳": c["next_trigger"][:40] + "…" if len(c["next_trigger"]) > 40 else c["next_trigger"],
        })
    
    df = pd.DataFrame(rows).sort_values("信号强度", ascending=False)
    
    # Color-coded table
    def color_score(val):
        if val >= 70: return f'color:#c2ef4e;font-weight:bold'
        if val >= 40: return 'color:#efc24e'
        return 'color:#8888a0'
    
    def color_trl(val):
        if 5 <= val <= 7: return f'color:#c2ef4e;font-weight:bold'
        if val >= 8: return 'color:#4ec2ef'
        return 'color:#8888a0'
    
    styled = df.style.map(color_score, subset=["信号强度"]).map(color_trl, subset=["TRL"])
    st.dataframe(styled, use_container_width=True, hide_index=True)
    
    # Summary insights
    hot_chains = df[df["信号强度"] >= 50]
    sweet_spot = df[(df["TRL"] >= 5) & (df["TRL"] <= 7) & (df["信号强度"] >= 30)]
    
    c1, c2 = st.columns(2)
    with c1:
        st.metric("🔥 高热度链", len(hot_chains), help="信号强度 ≥ 50")
    with c2:
        st.metric("🎯 甜蜜点链", len(sweet_spot), help="TRL 5-7 且信号 ≥ 30——最值得关注")


def render_bottleneck_alerts(chains):
    """Highlight chains stuck at critical TRL junctions."""
    stuck = [c for c in chains["chains"] if 5 <= c["trl"] < 7]
    early = [c for c in chains["chains"] if c["trl"] < 5]
    
    for c in stuck:
        st.markdown(f"""
        <div class="alert-box">
          <div class="title">⚠️ 瓶颈预警: {c['name']} — TRL {c['trl']:.1f}</div>
          <div class="body">卡在: {c['bottleneck']}<br>触发条件: {c['next_trigger']}<br>一旦突破: {c['opportunity_signal']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    if early:
        st.markdown("---")
        st.markdown("**🔭 早期跟踪（TRL < 5）：**")
        for c in early:
            st.markdown(f"- **{c['name']}** (TRL {c['trl']:.1f}): {c['next_trigger']}")


def main():
    signals, trl_data, chains, processed_at = load_all()
    
    st.markdown('<h1 style="color:#c2ef4e">📡 行业趋势监控 <span style="font-size:16px;color:#8888a0;font-weight:normal">技术链驱动的机会识别</span></h1>', unsafe_allow_html=True)
    st.markdown(f'<span style="color:#8888a0">AI · 医疗 · 航天 · 低空经济 ｜ {processed_at[:16] if processed_at else "—"}</span>', unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    
    if not signals:
        st.warning("暂无数据。运行 `python processors/run_pipeline.py`")
        return
    
    items = signals.get("signals", [])
    
    # ── ROW 1: CONCLUSION ──
    conclusion = render_conclusion(signals, chains, items)
    st.markdown(f'<div class="conclusion"><h2>📊 综合研判</h2><p>{conclusion}</p></div>', unsafe_allow_html=True)
    
    # ── ROW 2: TECH CHAIN PROGRESS ──
    st.markdown('<h3 style="color:#c2ef4e">🧬 技术链进度</h3>', unsafe_allow_html=True)
    render_chain_progress(chains, items)
    
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    
    # ── ROW 3: OPPORTUNITY MATRIX ──
    st.markdown('<h3 style="color:#c2ef4e">🎯 机会矩阵</h3>', unsafe_allow_html=True)
    st.caption("TRL 5-7 是最佳窗口（技术验证完毕，市场尚未爆发）")
    render_opportunity_matrix(chains, items)
    
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    
    # ── ROW 4: BOTTLENECKS ──
    st.markdown('<h3 style="color:#c2ef4e">⚠️ 瓶颈预警</h3>', unsafe_allow_html=True)
    render_bottleneck_alerts(chains)
    
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.caption("Hermes 行业趋势监控 v2 · 框架 v3 · `python processors/run_pipeline.py` 刷新数据")


if __name__ == "__main__":
    main()
