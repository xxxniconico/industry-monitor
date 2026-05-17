#!/usr/bin/env python3
# Dependencies: streamlit, pandas
"""Industry Monitor v4 — 行业优先 · 依赖网络 · 远期预测 :8505"""

import json
from pathlib import Path
from collections import Counter, defaultdict

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
PROCESSED, MODELS = ROOT / "data" / "processed", ROOT / "data" / "models"

IND = {"AI": "🤖 AI", "medical": "🏥 医疗", "space": "🚀 航天", "drone": "🚁 低空"}
SIG_EMOJI = {"技术链":"🧬","资本":"💰","技术":"🔬","监管":"📋","市场":"📊","人才":"👥","基建":"🏗️"}
TIER = {
    "short":  {"label":"短期 0-12月","color":"#ef6060","bg":"#3a2020","desc":"瓶颈·产能·即刻"},
    "medium": {"label":"中期 1-3年","color":"#efc24e","bg":"#3a3020","desc":"替代·拐点·布局"},
    "long":   {"label":"长期 3-10年","color":"#4ec2ef","bg":"#203040","desc":"范式·预测·前瞻"}
}

st.set_page_config(page_title="行业趋势监控", page_icon="📡", layout="wide")
st.markdown("""<style>
.stApp { background: #1f1633; }
.conclusion { background:linear-gradient(135deg,#2a1f40,#1f1633); border:1px solid #c2ef4e; border-radius:12px; padding:20px; margin-bottom:12px; }
.conclusion h3 { color:#c2ef4e; margin:0 0 6px 0; }
.conclusion .body { color:#c8c8d0; font-size:14px; line-height:1.6; }
.ind-section { margin:16px 0; }
.ind-title { color:#c2ef4e; font-size:20px; font-weight:bold; margin-bottom:4px; }
.tier-label { display:inline-block; padding:2px 10px; border-radius:10px; font-size:11px; font-weight:bold; margin-right:6px; }
.primary-chain { background:#2a1f40; border-radius:8px; padding:10px 14px; margin:4px 0; border-left:4px solid; }
.secondary-chain { background:#252035; border-radius:8px; padding:8px 14px; margin:4px 0; border-left:3px solid; opacity:0.92; }
.chain-name { font-size:14px; font-weight:bold; }
.chain-trig { color:#a0a0b0; font-size:11px; margin-top:2px; }
.chain-bar { display:flex;align-items:center;gap:6px;margin-top:4px; }
.dep-row { font-size:11px; color:#8888a0; margin-top:4px; }
.dep-row span { color:#a0a0a0; }
.dep-arrow { color:#666688; margin:0 4px; }
.prediction-box { background:linear-gradient(135deg,#1a2a3a,#1f1633); border:1px dashed #4ec2ef; border-radius:8px; padding:12px; margin:8px 0; }
.prediction-box .pred-title { color:#4ec2ef; font-weight:bold; font-size:13px; }
.prediction-box .pred-body { color:#a0c0d0; font-size:12px; margin-top:4px; line-height:1.5; }
.score-badge { font-size:22px; font-weight:bold; text-align:center; }
.matrix-table { font-size:13px; }
hr.div { border-color:#333355; margin:14px 0; }
</style>""", unsafe_allow_html=True)


@st.cache_data(ttl=60)
def load_all():
    sp = PROCESSED / "signals.json"; cp = MODELS / "tech_chains.json"
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
    total = int(((signal_score + boost) * 0.6 + trl_score * 0.4) * urgency)
    return min(100, max(5, total)), matches, cap


def render_conclusion(chains, items):
    chain_map = {c["id"]: c for c in chains["chains"]}
    scored = [(c, *score_chain(c, items)) for c in chains["chains"]]
    scored.sort(key=lambda x: -x[2])
    
    # Top short + their dependents
    short_top = [(c,s,m,cap) for c,s,m,cap in scored if c["tier"]=="short"][:3]
    
    lines = [f"**今日 {len(items)} 条信号。** 短期链信号最活跃，长期链需前瞻布局。\n"]
    lines.append("### 🔴 即刻关注")
    
    for c, s, m, cap in short_top:
        bar = "█"*int(c["trl"]) + "░"*(9-int(c["trl"]))
        driven = [chain_map[d]["name"] for d in c.get("drives",[]) if d in chain_map]
        dep_str = f" → 带动: {', '.join(driven)}" if driven else ""
        lines.append(f"- **{c['name']}** TRL {c['trl']:.1f} `{bar}` · 信号 {m} · 资本 {cap} · 机会分 **{s}**{dep_str}")
    
    # Dependency insight
    lines.append("")
    lines.append("### 🔗 关键依赖链")
    # Find CoWoS chain
    cowos = chain_map.get("short-cowos")
    if cowos:
        driven = [(chain_map[d]["name"], *score_chain(chain_map[d], items)) for d in cowos.get("drives",[]) if d in chain_map]
        dep_str = " → ".join([f"{n}({sc[0]})" for n, *sc in driven])
        lines.append(f"- **CoWoS 产能** 是总阀门 → {dep_str}")
    
    # Prediction highlight
    lines.append("")
    lines.append("### 🔮 远期预测亮点")
    preds = [c for c in chains["chains"] if c.get("prediction")]
    for c in preds[:2]:
        lines.append(f"- **{c['name']}**: {c['prediction'][:100]}…")
    
    return "\n".join(lines)


def render_industry_section(chains, items, industry):
    ind_chains = [c for c in chains["chains"] if c["industry"] == industry]
    if not ind_chains: return
    
    chain_map = {c["id"]: c for c in chains["chains"]}
    
    # Group by tier
    for tier_key in ["short", "medium", "long"]:
        tier_chains = [c for c in ind_chains if c["tier"] == tier_key]
        if not tier_chains: continue
        
        t = TIER[tier_key]
        
        # Sort primary first
        tier_chains.sort(key=lambda c: (0 if c["role"]=="primary" else 1, -c["trl"]))
        
        st.markdown(f'<span class="tier-label" style="background:{t["bg"]};color:{t["color"]};">{t["label"]}</span> <span style="color:#8888a0;font-size:12px;">{t["desc"]}</span>', unsafe_allow_html=True)
        
        for c in tier_chains:
            score, matches, cap = score_chain(c, items)
            pct = c["trl"] / 9
            color = t["color"]
            is_primary = c["role"] == "primary"
            card_class = "primary-chain" if is_primary else "secondary-chain"
            
            # Dependencies
            deps = [chain_map[d]["name"] for d in c.get("depends_on",[]) if d in chain_map]
            driven = [chain_map[d]["name"] for d in c.get("drives",[]) if d in chain_map]
            
            cols = st.columns([4, 0.6])
            with cols[0]:
                role_icon = "◆" if is_primary else "◇"
                st.markdown(f"""
                <div class="{card_class}" style="border-left-color:{color};">
                  <div class="chain-name" style="color:{color};">{role_icon} {c['name']}</div>
                  <div class="chain-bar">
                    <span style="color:#8888a0;font-size:10px;width:40px;">TRL {c['trl']:.1f}</span>
                    <div style="flex:1;height:6px;background:#333355;border-radius:3px;">
                      <div style="width:{pct*100}%;height:6px;background:{color};border-radius:3px;"></div>
                    </div>
                  </div>
                  <div class="chain-trig">🎯 {c['next_trigger'][:90]}</div>
                  {f'<div class="dep-row"><span>↑ 依赖:</span> {", ".join(deps)}</div>' if deps else ''}
                  {f'<div class="dep-row"><span>↓ 驱动:</span> {", ".join(driven)}</div>' if driven else ''}
                </div>
                """, unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f'<div class="score-badge" style="color:{color};">{score}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="text-align:center;font-size:10px;color:#8888a0;">信{matches}·资{cap}</div>', unsafe_allow_html=True)
            
            # Bottleneck
            if 5 <= c["trl"] < 7 and tier_key != "long":
                st.markdown(f'<div style="background:#332040;border-left:3px solid #ef8f4e;padding:6px 12px;border-radius:4px;margin:2px 0 6px 0;font-size:12px;color:#d0c0a0;">⚠️ {c["bottleneck"]}</div>', unsafe_allow_html=True)
            
            # Prediction for long-term chains
            if c.get("prediction"):
                st.markdown(f"""
                <div class="prediction-box">
                  <div class="pred-title">🔮 远期预测</div>
                  <div class="pred-body">{c['prediction']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)


def render_matrix(chains, items):
    rows = []
    for c in chains["chains"]:
        score, matches, cap = score_chain(c, items)
        t = TIER[c["tier"]]
        rows.append({
            "行业": IND.get(c["industry"],""), "层级": t["label"], "技术链": c["name"],
            "角色": "主" if c["role"]=="primary" else "辅", "TRL": c["trl"],
            "机会分": score, "信号": matches, "资本": cap,
        })
    df = pd.DataFrame(rows).sort_values("机会分", ascending=False)
    
    def color_score(val):
        if val >= 70: return 'color:#c2ef4e;font-weight:bold'
        if val >= 40: return 'color:#efc24e'
        return 'color:#8888a0'
    
    st.dataframe(df.style.map(color_score, subset=["机会分"]), use_container_width=True, hide_index=True)
    
    c1, c2, c3 = st.columns(3)
    total_chains = len(rows)
    primary = len([r for _,r in df.iterrows() if r["角色"]=="主"])
    c1.metric("总链数", total_chains)
    c2.metric("主链", primary, help="直接驱动的核心链")
    c3.metric("辅链", total_chains - primary, help="依赖主链的传导链")


def main():
    signals, chains, processed_at = load_all()
    
    st.markdown('<h1 style="color:#c2ef4e;margin-bottom:2px;">📡 行业趋势监控</h1>', unsafe_allow_html=True)
    st.markdown(f'<span style="color:#8888a0;font-size:13px;">行业优先 · 依赖网络 · 远期预测 ｜ {processed_at[:16] if processed_at else "—"}</span>', unsafe_allow_html=True)
    st.markdown('<hr class="div">', unsafe_allow_html=True)
    
    if not signals:
        st.warning("暂无数据")
        return
    
    items = signals.get("signals", [])
    
    # ── CONCLUSION ──
    conclusion = render_conclusion(chains, items)
    st.markdown(f'<div class="conclusion"><h3>📊 综合研判</h3><div class="body">{conclusion}</div></div>', unsafe_allow_html=True)
    
    # ── INDUSTRY SECTIONS ──
    for ind_key in ["AI", "medical", "space", "drone"]:
        st.markdown(f'<div class="ind-title">{IND[ind_key]}</div>', unsafe_allow_html=True)
        render_industry_section(chains, items, ind_key)
        st.markdown('<hr class="div">', unsafe_allow_html=True)
    
    # ── MATRIX ──
    st.markdown(f'<div class="ind-title">🎯 全链矩阵</div>', unsafe_allow_html=True)
    render_matrix(chains, items)
    
    st.markdown('<hr class="div">', unsafe_allow_html=True)
    st.caption("Hermes 行业趋势监控 v4 · 15条链 · 主辅依赖 · 远期预测 · `python processors/run_pipeline.py` 刷新")


if __name__ == "__main__":
    main()
