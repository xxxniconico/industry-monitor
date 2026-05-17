#!/bin/bash
# daily_collect.sh — 每日数据采集（所有 collector）
# 由 cron 调用，输出到 data/raw/
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PYTHON="$HOME/.hermes/hermes-agent/venv/bin/python"
LOG="$ROOT/data/raw/_collect_log.txt"

cd "$ROOT"

echo "=== $(date -Iseconds) ===" | tee "$LOG"

# Step 1: RSS feeds (18 sources)
echo "[1/5] RSS monitor..." | tee -a "$LOG"
"$VENV_PYTHON" collectors/rss_monitor.py 2>&1 | tee -a "$LOG"

# Step 2: arXiv papers (AI/tech)
echo "[2/5] arXiv paper tracker..." | tee -a "$LOG"
"$VENV_PYTHON" collectors/paper_tracker.py 2>&1 | tee -a "$LOG"

# Step 3: Clinical trials (medical)
echo "[3/5] Clinical trials..." | tee -a "$LOG"
"$VENV_PYTHON" collectors/clinical_trials.py 2>&1 | tee -a "$LOG"

# Step 4: Launch tracker (space)
echo "[4/5] Launch tracker..." | tee -a "$LOG"
"$VENV_PYTHON" collectors/launch_tracker.py 2>&1 | tee -a "$LOG"

# Step 5: VC news (capital)
echo "[5/5] VC tracker..." | tee -a "$LOG"
"$VENV_PYTHON" collectors/vc_tracker.py 2>&1 | tee -a "$LOG"

echo "=== Done $(date -Iseconds) ===" | tee -a "$LOG"
