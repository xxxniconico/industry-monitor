#!/usr/bin/env python3
# Dependencies: streamlit, pandas
"""Industry Monitor v3 — 三级技术链驱动的行业机会看板 :8505"""

import json
from pathlib import Path
from collections import Counter

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
MODELS = ROOT / "data" / "models"

IND = {"AI": "🤖 AI", "medical": "🏥 医疗", "space": "🚀 航天", "drone": "🚁 低空"}
SIG_EMOJI = {"技术链":"🧬","资本":"💰","技术":"🔬","监管":"📋","市场":"📊","人才":"👥","基建":"🏗️"}
TIER = {"short":{"label":"短期 0-12月","color":"#ef6060","bg":"#3a2020"},
        "medium":{"label":"中期 1-3年","color":"#efc24e","bg":"#3a3020"},
        "long":{"label":"长期 3-10年","color":"#4ec2ef","bg":"#203040"}}

# ── Theme ──
st.set_page_config(page_title="行业趋势监控", page_icon="📡", layout="wide")
st.markdown("""<style>
.stApp { background: #1f1633; }
.conclusion { background:linear-gradient(135deg,#2a1f40,#1f1633); border:1px solid #c2ef4e; border-radius:12px; padding:24px; margin-bottom:12px; }
.conclusion h2 { color:#c2ef4e; margin:0 0 6px 0; }
.conclusion .hot { color:#c8c8d0; font-size:14px; line-height:1.6; }
.chain-row { display:flex; align-items:center; gap:10px; padding:8px 12px; background:#2a1f40; border-radius:6px; margin:4px 0; }
.chain-row .tier-dot { width:10px; height:10px; border-radius:50%; flex-shrink:0; }
.chain-row .info { flex:1; min-width:0; }
.chain-row .name { color:#c8c8d0; font-size:14px; font-weight:bold; }
.chain-row .trig { color:#8888a0; font-size:11px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.chain-row .score { font-size:18px; font-weight:bold; width:40px; text-align:center; flex-shrink:0; }
.bottleneck-box { background:#332040; border-left:3px solid #ef8f4e; padding:8px 12px; border-radius:4px; margin:4px 0; font-size:12px; color:#d0c0a0; }
.alert { background:#3a2020; border-left:3px solid #ef6060; padding:8px 12px; border-radius:4px; margin:4px 0; font-size:12px; }
.alert .a-title { color:#ef6060; font-weight:bold; }
.alert .a-body { color:#c8a0a0; }
hr.divider { border-color:#333355; margin:16px 0; }
.section-title { color:#c2ef4e; margin:16px 0 8px 0; }
.tier-header { display:flex;align-items:center;gap:8px;margin:12px 0 6px 0; }
.tier-header .dot { width:12px;height:12px;border-radius:50%; }
.tier-header .label { color:#c8c8d0;font-size:15px;font-weight:bold; }
.tier-header .desc { color:#8888a0;font-size:12px; }
.highlight { color:#c2ef4e; font-weight:bold; }
</style>""", unsafe_allow_html=True)


@st.cache_data(ttl=60)
def load_all():
    sp, tp, cp = PROCESSED/"signals.json", PROCESSED/"trl_tracker.json", MODELS/"tech_chains.json"
    if not sp.exists(): return None, None, None, None
    signals = json.loads(sp.read_text())
    trl_data = json.loads(tp.read_text()) if tp.exists() else {}
    chains = json.loads(cp.read_text()) if cp.exists() else {"chains":[]}
    return signals, trl_data, chains, signals.get("processed_at","")


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
    
    # Short-term chains get urgency bonus
    urgency = 1.2 if chain.get("tier") == "short" else 1.0
    
    total = int(((signal_score + boost) * 0.6 + trl_score * 0.4) * urgency)
    return min(100, max(5, total)), matches, cap


def render_conclusion(chains, items):
    chain_scores = [(c, *score_chain(c, items)) for c in chains["chains"]]
    chain_scores.sort(key=lambda x: -x[2])
    
    # Top short-term opportunity
    short_hot = [(c,s,m,cap) for c,s,m,cap in chain_scores if c["tier"]=="short"][:3]
    med_hot = [(c,s,m,cap) for c,s,m,cap in chain_scores if c["tier"]=="medium"][:2]
    
    lines = [f"**今日 {len(items)} 条信号。**"]
    
    if short_hot:
        lines.append("")
        lines.append("### 🔴 短期 — 即刻关注")
        for c, s, m, cap in short_hot:
            bar = "█"*int(c["trl"]) + "░"*(9-int(c["trl"]))
            lines.append(f"- <span class='highlight'>{c['name']}</span> TRL {c['trl']:.1f} `{bar}` · 信号 {m} 条 · 资本 {cap} 条 · 机会分 **{s}**")
            lines.append(f"  🎯 {c['next_trigger']}")
    
    if med_hot:
        lines.append("")
        lines.append("### 🟡 中期 — 布局窗口")
        for c, s, m, cap in med_hot:
            lines.append(f"- **{c['name']}** (TRL {c['trl']:.1f}) · 信号 {m} · 机会分 {s}")
    
    # Stuck chains
    stuck = [c for c in chains["chains"] if 5 <= c["trl"] < 7 and c["tier"] in ("short","medium")]
    if stuck:
        lines.append("")
        lines.append("### ⚠️ 卡在关键节点")
        for c in stuck[:2]:
            lines.append(f"- **{c['name']}**: {c['bottleneck']}")
    
    return "\n".join(lines)


def render_chain_list(chains, items, tier_filter=None):
    for c in chains["chains"]:
        if tier_filter and c["tier"] != tier_filter: continue
        score, matches, cap = score_chain(c, items)
        t = TIER.get(c["tier"], TIER["medium"])
        trl = c["trl"]
        pct = trl / 9
        
        cols = st.columns([0.05, 2, 0.6])
        with cols[0]:
            st.markdown(f'<div style="width:10px;height:10px;border-radius:50%;background:{t["color"]};margin-top:8px;"></div>', unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f"""
            <div style="color:#c8c8d0;font-size:14px;font-weight:bold;">{c['name']} 
              <span style="color:{t['color']};font-size:11px;">{t['label']} · {IND.get(c['industry'],'')}</span>
            </div>
            <div style="display:flex;align-items:center;gap:6px;margin-top:2px;">
              <span style="color:#8888a0;font-size:11px;width:40px;">TRL {trl:.1f}</span>
              <div style="flex:1;height:6px;background:#333355;border-radius:3px;">
                <div style="width:{pct*100}%;height:6px;background:{t['color']};border-radius:3px;"></div>
              </div>
            </div>
            <div style="color:#8888a0;font-size:11px;margin-top:2px;">🎯 {c['next_trigger'][:80]}{'…' if len(c['next_trigger'])>80 else ''}</div>
            """, unsafe_allow_html=True)
        with cols[2]:
            st.markdown(f'<div style="text-align:center;font-size:24px;font-weight:bold;color:{t["color"]};">{score}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="text-align:center;font-size:10px;color:#8888a0;">信号{matches}·资本{cap}</div>', unsafe_allow_html=True)
        
        if 5 <= trl < 7 and c["tier"] != "long":
            st.markdown(f'<div class="bottleneck-box">⚠️ 瓶颈: {c["bottleneck"]}</div>', unsafe_allow_html=True)


def render_opportunity_matrix(chains, items):
    rows = []
    for c in chains["chains"]:
        score, matches, cap = score_chain(c, items)
        t = TIER.get(c["tier"], TIER["medium"])
        rows.append({
            "层级": t["label"],
            "技术链": c["name"],
            "行业": IND.get(c["industry"],""),
            "TRL": c["trl"],
            "机会分": score,
            "信号": matches,
            "资本": cap,
            "下一跳": c["next_trigger"][:50],
        })
    df = pd.DataFrame(rows).sort_values("机会分", ascending=False)
    
    def color_score(val):
        if val >= 70: return 'color:#c2ef4e;font-weight:bold'
        if val >= 40: return 'color:#efc24e'
        return 'color:#8888a0'
    def color_trl(val):
        if 5 <= val <= 7: return 'color:#c2ef4e;font-weight:bold'
        if val >= 8: return 'color:#4ec2ef'
        return 'color:#8888a0'
    
    st.dataframe(df.style.map(color_score, subset=["机会分"]).map(color_trl, subset=["TRL"]), use_container_width=True, hide_index=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        short_hot = len([r for _,r in df.iterrows() if "短期" in str(r["层级"]) and r["机会分"] >= 50])
        st.metric("🔴 短期热链", short_hot)
    with c2:
        sweet = len([r for _,r in df.iterrows() if 5 <= r["TRL"] <= 7 and r["机会分"] >= 40])
        st.metric("🎯 甜蜜点", sweet, help="TRL 5-7 + 机会分 ≥ 40")
    with c3:
        converging = len([r for _,r in df.iterrows() if r["信号"] >= 3 and r["资本"] >= 2])
        st.metric("⚡ 资本+信号共振", converging)


def render_alerts(chains, items):
    stuck_short = [c for c in chains["chains"] if 5 <= c["trl"] < 7 and c["tier"] == "short"]
    for c in stuck_short:
        score, _, _ = score_chain(c, items)
        st.markdown(f"""
        <div class="alert">
          <div class="a-title">⚠️ 短期瓶颈: {c['name']} — TRL {c['trl']:.1f} · 机会分 {score}</div>
          <div class="a-body">卡在: {c['bottleneck']}<br>一旦突破 — {c['opportunity_signal']}</div>
        </div>
        """, unsafe_allow_html=True)


def main():
    signals, trl_data, chains, processed_at = load_all()
    
    st.markdown(f'<h1 style="color:#c2ef4e;margin-bottom:2px;">📡 行业趋势监控</h1>', unsafe_allow_html=True)
    st.markdown(f'<span style="color:#8888a0;font-size:13px;">技术链驱动的机会识别 · 短期/中期/长期分层 ｜ {processed_at[:16] if processed_at else "—"}</span>', unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    
    if not signals:
        st.warning("暂无数据。运行 `python processors/run_pipeline.py`")
        return
    
    items = signals.get("signals", [])
    
    # ── CONCLUSION ──
    conclusion = render_conclusion(chains, items)
    st.markdown(f'<div class="conclusion"><h2>📊 综合研判</h2><div class="hot">{conclusion}</div></div>', unsafe_allow_html=True)
    
    # ── TECH CHAINS BY TIER ──
    for tier_key in ["short", "medium", "long"]:
        t = TIER[tier_key]
        st.markdown(f"""
        <div class="tier-header">
          <div class="dot" style="background:{t['color']};"></div>
          <span class="label">{t['label']}</span>
          <span class="desc">— {t['desc']}</span>
        </div>
        """, unsafe_allow_html=True)
        render_chain_list(chains, items, tier_filter=tier_key)
    
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    
    # ── OPPORTUNITY MATRIX ──
    st.markdown('<h3 class="section-title">🎯 全链机会矩阵</h3>', unsafe_allow_html=True)
    render_opportunity_matrix(chains, items)
    
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    
    # ── ALERTS ──
    st.markdown('<h3 class="section-title">⚠️ 瓶颈预警</h3>', unsafe_allow_html=True)
    render_alerts(chains, items)
    
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.caption("Hermes 行业趋势监控 v3 · 15条技术链（5短期+5中期+5长期）· `python processors/run_pipeline.py` 刷新")


if __name__ == "__main__":
    main()
