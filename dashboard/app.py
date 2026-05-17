#!/usr/bin/env python3
# Dependencies: streamlit, pandas
"""Industry Monitor — 跨行业趋势监控看板 :8505"""

import json
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"

INDUSTRY_LABELS = {"AI": "AI", "medical": "医疗", "space": "航天", "drone": "低空经济"}
SIGNAL_ORDER = ["技术链", "资本", "技术", "监管", "市场", "人才", "基建"]
SIGNAL_EMOJI = {"技术链": "🧬", "资本": "💰", "技术": "🔬", "监管": "📋", "市场": "📊", "人才": "👥", "基建": "🏗️"}
S_CURVE = {"AI": "早期大众 · 增长期", "medical": "早期采纳→早期大众", "space": "早期采纳 · 扩张", "drone": "创新者→早期采纳"}

# ── Sentry dark theme ──
DARK_BG = "#1f1633"
GREEN = "#c2ef4e"
CARD_BG = "#2a1f40"

st.set_page_config(page_title="行业趋势监控", page_icon="📡", layout="wide")

st.markdown(f"""
<style>
  .stApp {{ background: {DARK_BG}; }}
  .conclusion-card {{
    background: linear-gradient(135deg, #2a1f40, #1f1633);
    border: 1px solid {GREEN};
    border-radius: 12px; padding: 24px; margin-bottom: 20px;
  }}
  .conclusion-card h2 {{ color: {GREEN}; margin-top: 0; }}
  .conclusion-card p {{ color: #c8c8d0; font-size: 15px; line-height: 1.7; }}
  .industry-card {{
    background: {CARD_BG}; border-radius: 10px;
    padding: 18px; margin-bottom: 12px; border-left: 4px solid {GREEN};
  }}
  .industry-card h4 {{ color: {GREEN}; margin: 0 0 8px 0; }}
  .industry-card .pos {{ color: #a0a0b0; font-size: 13px; }}
  .alert-item {{ color: #f0a060; font-size: 14px; padding: 4px 0; }}
  .metric-value {{ color: {GREEN}; font-size: 28px; font-weight: bold; }}
  .metric-label {{ color: #8888a0; font-size: 12px; }}
  .section-divider {{ border-top: 1px solid #333355; margin: 24px 0; }}
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=60)
def load_all():
    signals_path = PROCESSED / "signals.json"
    trl_path = PROCESSED / "trl_tracker.json"
    if not signals_path.exists():
        return None, None, None
    signals = json.loads(signals_path.read_text())
    trl = json.loads(trl_path.read_text()) if trl_path.exists() else {}
    return signals, trl, signals.get("processed_at", "")


def build_conclusion(signals: dict, trl: dict) -> str:
    """Generate natural-language conclusion from signal data."""
    items = signals.get("signals", [])
    by_type = signals.get("by_type", {})
    total = len(items)

    # Industry breakdown
    ind_counter = Counter(s.get("industry") for s in items)
    ai_n = ind_counter.get("AI", 0)
    med_n = ind_counter.get("medical", 0)
    space_n = ind_counter.get("space", 0)
    drone_n = ind_counter.get("drone", 0)

    # Dominant signal types
    top_types = sorted(by_type.items(), key=lambda x: -x[1])[:3]
    type_str = " · ".join(f"{SIGNAL_EMOJI.get(t,'')} {t}({n}条)" for t, n in top_types)

    # TRL snapshot
    avg_trl = trl.get("industry_avg_trl", {})
    trl_lines = []
    for ind, label in [("AI", "AI"), ("space", "航天"), ("medical", "医疗"), ("drone", "低空")]:
        v = avg_trl.get(ind)
        trl_lines.append(f"{label} TRL {v:.1f}" if v is not None else f"{label} —")

    # Growth signals (capital + tech chain both active = inflection)
    capital_tech = len([s for s in items if s.get("signal_type") in ("资本", "技术链")])
    regulation = by_type.get("监管", 0)

    # Build conclusion
    parts = [
        f"**今日采集 {total} 条信号**，覆盖 AI({ai_n})、医疗({med_n})、航天({space_n})、低空经济({drone_n}) 四个行业。",
        f"主导信号类型：{type_str}。",
        f"行业技术就绪度：{' · '.join(trl_lines)}。",
    ]

    if capital_tech >= 15:
        parts.append("⚠️ **资本 + 技术链信号活跃**——多个行业处于技术验证→产品化的关键跳跃期，值得重点关注。")
    if regulation >= 30:
        parts.append("📋 监管信号密集出现，政策窗口可能在打开。")

    # Find converging signals
    ai_cap = len([s for s in items if s.get("industry") == "AI" and s.get("signal_type") == "资本"])
    space_infra = len([s for s in items if s.get("industry") == "space" and s.get("signal_type") == "基建"])
    drone_reg = len([s for s in items if s.get("industry") == "drone" and s.get("signal_type") == "监管"])

    alerts = []
    if ai_cap >= 5:
        alerts.append("🤖 AI 资本持续涌入，算力基础设施链仍是主战场。")
    if space_infra >= 3:
        alerts.append("🚀 航天基建信号增多，关注 Starship 商用节点和发射产能扩张。")
    if drone_reg >= 3:
        alerts.append("🚁 低空经济监管动作频繁，适航证和空域开放是关键催化剂。")

    if alerts:
        parts.append("")
        parts.extend(alerts)

    parts.append(f"\n📌 **当前阶段判断：** AI 处于早期大众增长期（S曲线中段），医疗从早期采纳向大众过渡，航天处于扩张期，低空经济正在跨越从创新者到早期采纳的鸿沟。")

    return "\n\n".join(parts)


def main():
    signals, trl, processed_at = load_all()

    # ── Header ──
    st.markdown(f'<h1 style="color:{GREEN}">📡 行业趋势监控</h1>', unsafe_allow_html=True)
    st.markdown(
        f'<span style="color:#8888a0">AI · 医疗 · 航天 · 低空经济 ｜ 更新于 {processed_at[:16] if processed_at else "—"}</span>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    if not signals:
        st.warning("暂无数据。运行 `python processors/run_pipeline.py`")
        return

    # ── CONCLUSION ──
    conclusion = build_conclusion(signals, trl)
    st.markdown(f"""
    <div class="conclusion-card">
      <h2>📊 综合研判</h2>
      <p>{conclusion.replace(chr(10), '<br>')}</p>
    </div>
    """, unsafe_allow_html=True)

    # ── FOUR INDUSTRY CARDS ──
    items = signals.get("signals", [])
    avg_trl = trl.get("industry_avg_trl", {})
    ind_items = {"AI": [], "space": [], "medical": [], "drone": []}
    for s in items:
        ind = s.get("industry", "")
        if ind in ind_items:
            ind_items[ind].append(s)

    cols = st.columns(4)
    for i, (ind, label) in enumerate([("AI", "🤖 AI"), ("medical", "🏥 医疗"), ("space", "🚀 航天"), ("drone", "🚁 低空经济")]):
        its = ind_items[ind]
        type_counts = Counter(s.get("signal_type") for s in its)
        top3 = type_counts.most_common(3)
        trl_val = avg_trl.get(ind)

        with cols[i]:
            st.markdown(f"""
            <div class="industry-card">
              <h4>{label}</h4>
              <div class="pos">📍 {S_CURVE.get(ind, '—')}</div>
              <div style="margin-top:10px;font-size:13px;color:#c8c8d0;">
                {"<br>".join(f"{SIGNAL_EMOJI.get(t,'')} {t}: {n}" for t,n in top3) if top3 else "暂无信号"}
              </div>
              <div style="margin-top:8px;">
                <span class="metric-value">{trl_val:.1f}</span>
                <span class="metric-label"> avg TRL</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── CROSS-SIGNAL TABLE ──
    st.markdown(f'<h3 style="color:{GREEN}">⚡ 跨信号交叉分析</h3>', unsafe_allow_html=True)

    cross_rows = []
    for ind, label in [("AI", "AI"), ("space", "航天"), ("medical", "医疗"), ("drone", "低空")]:
        its = ind_items[ind]
        tc = Counter(s.get("signal_type") for s in its)
        capital = tc.get("资本", 0)
        tech = tc.get("技术", 0)
        reg = tc.get("监管", 0)
        infra = tc.get("基建", 0)
        talent = tc.get("人才", 0)
        tech_chain = tc.get("技术链", 0)

        # Confluence check
        signals_active = []
        if capital >= 5: signals_active.append("💰资本")
        if tech >= 20: signals_active.append("🔬技术")
        if reg >= 5: signals_active.append("📋监管")
        if infra >= 3: signals_active.append("🏗️基建")

        confluence = "🟢 多信号共振" if len(signals_active) >= 3 else ("🟡 信号分散" if len(signals_active) >= 2 else "🔴 信号稀疏")

        cross_rows.append({
            "行业": label,
            "💰资本": capital,
            "🔬技术": tech,
            "📋监管": reg,
            "🏗️基建": infra,
            "👥人才": talent,
            "🧬技术链": tech_chain,
            "交叉判断": f"{confluence} ({'+'.join(signals_active) if signals_active else '—'})",
        })

    cross_df = pd.DataFrame(cross_rows)
    st.dataframe(cross_df, use_container_width=True, hide_index=True)

    # ── HIGHLIGHTS ──
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown(f'<h3 style="color:{GREEN}">🔔 重点信号</h3>', unsafe_allow_html=True)

    high_conf = sorted(items, key=lambda x: x.get("confidence", 0), reverse=True)[:10]
    for s in high_conf:
        stype = s.get("signal_type", "")
        emoji = SIGNAL_EMOJI.get(stype, "")
        st.markdown(f'<div class="alert-item">{emoji} <b>[{INDUSTRY_LABELS.get(s.get("industry",""),"")}]</b> {s.get("title","")}</div>', unsafe_allow_html=True)

    # ── FOOTER ──
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.caption("Hermes 行业趋势监控 · 框架 v3 · 信号刷新：运行 `python processors/run_pipeline.py`")


if __name__ == "__main__":
    main()
