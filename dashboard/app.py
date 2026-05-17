#!/usr/bin/env python3
# Dependencies: streamlit (uv pip install streamlit)
"""Industry Monitor dashboard — port 8505."""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"

INDUSTRY_LABELS = {
    "AI": "AI",
    "medical": "医疗",
    "space": "航天",
    "drone": "低空经济",
}

SIGNAL_ORDER = ["技术链", "资本", "技术", "监管", "市场", "人才", "基建"]

COLLECTOR_LABELS = {
    "arxiv": "arXiv",
    "rss": "RSS",
    "clinicaltrials": "临床试验",
    "launch_library": "发射库",
    "vc_news": "VC 新闻",
}


@st.cache_data(ttl=60)
def load_json(filename: str) -> dict | None:
    path = PROCESSED / filename
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def signals_df(signals_data: dict) -> pd.DataFrame:
    df = pd.DataFrame(signals_data.get("signals") or [])
    if df.empty:
        return df
    df["industry_label"] = df["industry"].map(lambda x: INDUSTRY_LABELS.get(x, x))
    df["collector_label"] = df["collector"].map(lambda x: COLLECTOR_LABELS.get(x, x))
    return df


def trl_df(trl_data: dict) -> pd.DataFrame:
    df = pd.DataFrame(trl_data.get("items") or [])
    if df.empty:
        return df
    df["industry_label"] = df["industry"].map(lambda x: INDUSTRY_LABELS.get(x, x))
    return df


def events_df(events_data: dict) -> pd.DataFrame:
    df = pd.DataFrame(events_data.get("events") or [])
    if df.empty:
        return df
    df["industry_label"] = df["industry"].map(lambda x: INDUSTRY_LABELS.get(x, x))
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True)
    return df


def apply_filters(df: pd.DataFrame, industries: list, types: list, collectors: list, min_conf: float) -> pd.DataFrame:
    out = df.copy()
    if industries:
        out = out[out["industry"].isin(industries)]
    if types and "signal_type" in out.columns:
        out = out[out["signal_type"].isin(types)]
    if collectors:
        out = out[out["collector"].isin(collectors)]
    if "confidence" in out.columns:
        out = out[out["confidence"] >= min_conf]
    return out


def render_sidebar(df: pd.DataFrame) -> tuple[list, list, list, float]:
    st.sidebar.header("筛选")
    industries = st.sidebar.multiselect(
        "行业",
        options=sorted(df["industry"].dropna().unique()),
        format_func=lambda x: INDUSTRY_LABELS.get(x, x),
        default=[],
    )
    available_types = set(df["signal_type"].unique()) if "signal_type" in df.columns else set()
    types = st.sidebar.multiselect(
        "信号类型",
        options=[t for t in SIGNAL_ORDER if t in available_types],
        default=[],
    )
    collectors = st.sidebar.multiselect(
        "数据源",
        options=sorted(df["collector"].dropna().unique()),
        format_func=lambda x: COLLECTOR_LABELS.get(x, x),
        default=[],
    )
    min_conf = st.sidebar.slider("最低置信度", 0.0, 1.0, 0.0, 0.05)
    return industries, types, collectors, min_conf


def tab_overview(df: pd.DataFrame, trl_data: dict, processed_at: str) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("信号总数", len(df))
    c2.metric("行业数", df["industry"].nunique())
    c3.metric("数据源", df["collector"].nunique())
    c4.metric("处理时间", processed_at[:10] if processed_at else "—")

    left, right = st.columns(2)

    with left:
        st.subheader("信号类型分布")
        type_counts = df["signal_type"].value_counts().reindex(SIGNAL_ORDER).fillna(0).astype(int)
        st.bar_chart(type_counts)

    with right:
        st.subheader("行业分布")
        ind_counts = df.groupby("industry_label").size().sort_values(ascending=False)
        st.bar_chart(ind_counts)

    st.subheader("行业平均 TRL")
    avg = trl_data.get("industry_avg_trl") or {}
    if avg:
        trl_chart = pd.Series(
            {INDUSTRY_LABELS.get(k, k): v for k, v in avg.items()}
        ).sort_values(ascending=False)
        st.bar_chart(trl_chart)
    else:
        st.info("暂无 TRL 数据")


def tab_signals(df: pd.DataFrame) -> None:
    st.subheader(f"信号列表（{len(df)} 条）")
    display = df[
        ["title", "signal_type", "industry_label", "collector_label", "confidence", "published", "url"]
    ].copy()
    display.columns = ["标题", "信号", "行业", "来源", "置信度", "时间", "链接"]
    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "链接": st.column_config.LinkColumn("链接", display_text="打开"),
            "置信度": st.column_config.ProgressColumn("置信度", min_value=0, max_value=1),
        },
    )


def tab_trl(signals: pd.DataFrame, trl: pd.DataFrame) -> None:
    if trl.empty or "trl" not in trl.columns:
        st.info("暂无 TRL 数据，请先运行 `python processors/run_pipeline.py`")
        return
    merged = signals.merge(trl[["id", "trl", "rationale"]], on="id", how="left")
    merged = merged.dropna(subset=["trl"])
    st.subheader("TRL 分布")
    c1, c2 = st.columns(2)
    with c1:
        st.bar_chart(merged["trl"].value_counts().sort_index())
    with c2:
        by_ind = merged.groupby("industry_label")["trl"].mean().round(1).sort_values(ascending=False)
        st.bar_chart(by_ind)

    st.subheader("高 TRL 条目（≥7）")
    high = merged[merged["trl"] >= 7].sort_values("trl", ascending=False)
    if high.empty:
        st.info("当前筛选下无 TRL ≥ 7 的条目")
        return
    show = high[["title", "trl", "rationale", "industry_label", "url"]].head(50)
    show.columns = ["标题", "TRL", "依据", "行业", "链接"]
    st.dataframe(show, use_container_width=True, hide_index=True)


def tab_events(df: pd.DataFrame) -> None:
    st.subheader(f"事件时间线（{len(df)} 条）")
    if "date" in df.columns:
        df = df.sort_values("date", ascending=False, na_position="last")
    show = df[["date", "title", "signal_type", "industry_label", "collector", "url"]].head(200)
    show.columns = ["时间", "标题", "信号", "行业", "来源", "链接"]
    st.dataframe(
        show,
        use_container_width=True,
        hide_index=True,
        column_config={"链接": st.column_config.LinkColumn("链接", display_text="打开")},
    )


def main() -> None:
    st.set_page_config(
        page_title="Industry Monitor",
        page_icon="📡",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("Industry Monitor")
    st.caption("跨行业趋势监控 · AI / 医疗 / 航天 / 低空经济")

    signals_data = load_json("signals.json")
    trl_data = load_json("trl_tracker.json")
    events_data = load_json("events.json")

    if not signals_data:
        st.error("未找到 `data/processed/signals.json`，请先运行采集与处理管道：")
        st.code(
            "python collectors/run_all.py\npython processors/run_pipeline.py",
            language="bash",
        )
        return

    df = signals_df(signals_data)
    trl = trl_df(trl_data or {})
    events = events_df(events_data or {})
    processed_at = signals_data.get("processed_at", "")

    industries, types, collectors, min_conf = render_sidebar(df)
    filtered = apply_filters(df, industries, types, collectors, min_conf)

    if events_data and not events.empty:
        ev_mask = pd.Series(True, index=events.index)
        if industries:
            ev_mask &= events["industry"].isin(industries)
        if types:
            ev_mask &= events["signal_type"].isin(types)
        if collectors:
            ev_mask &= events["collector"].isin(collectors)
        events_filtered = events[ev_mask]
    else:
        events_filtered = events

    if trl_data and not trl.empty:
        trl_ids = set(filtered["id"])
        trl_filtered = trl[trl["id"].isin(trl_ids)]
    else:
        trl_filtered = trl

    tab1, tab2, tab3, tab4 = st.tabs(["总览", "信号", "TRL", "事件"])

    with tab1:
        tab_overview(filtered, trl_data or {}, processed_at)
    with tab2:
        tab_signals(filtered)
    with tab3:
        tab_trl(filtered, trl_filtered)
    with tab4:
        tab_events(events_filtered)


if __name__ == "__main__":
    main()
