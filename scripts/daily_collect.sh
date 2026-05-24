#!/bin/bash
# daily_collect.sh — 每日数据采集（所有 collector）
set -euo pipefail

ROOT="/home/xxxsuli/industry-monitor"
VENV_PYTHON="/home/xxxsuli/.hermes/hermes-agent/venv/bin/python"
LOG="$ROOT/data/raw/_collect_log.txt"

cd "$ROOT"

echo "=== $(date -Iseconds) ===" | tee "$LOG"

echo "[1/5] RSS monitor..." | tee -a "$LOG"
"$VENV_PYTHON" collectors/rss_monitor.py 2>&1 | tee -a "$LOG"

echo "[2/5] arXiv paper tracker..." | tee -a "$LOG"
"$VENV_PYTHON" collectors/paper_tracker.py 2>&1 | tee -a "$LOG"

echo "[3/5] Clinical trials..." | tee -a "$LOG"
"$VENV_PYTHON" collectors/clinical_trials.py 2>&1 | tee -a "$LOG"

echo "[4/5] Launch tracker..." | tee -a "$LOG"
"$VENV_PYTHON" collectors/launch_tracker.py 2>&1 | tee -a "$LOG"

echo "[5/5] VC tracker..." | tee -a "$LOG"
"$VENV_PYTHON" collectors/vc_tracker.py 2>&1 | tee -a "$LOG"

echo "=== Done $(date -Iseconds) ===" | tee -a "$LOG"
