#!/bin/bash
# daily_update.sh — 每日全链路更新（采集 + 流水线）
# 由 cron 调用，一步完成
set -euo pipefail

ROOT="/home/xxxsuli/industry-monitor"
VENV_PYTHON="/home/xxxsuli/.hermes/hermes-agent/venv/bin/python"
LOG="$ROOT/data/raw/_daily_update_log.txt"

cd "$ROOT"

echo "=== daily_update $(date -Iseconds) ===" | tee "$LOG"

# Step 1: Collect raw data
echo "--- Collect ---" | tee -a "$LOG"
"$VENV_PYTHON" collectors/run_all.py 2>&1 | tee -a "$LOG"

# Step 2: Run pipeline (classify → TRL → alerts)
echo "--- Pipeline ---" | tee -a "$LOG"
"$VENV_PYTHON" processors/run_pipeline.py 2>&1 | tee -a "$LOG"

echo "=== Done $(date -Iseconds) ===" | tee -a "$LOG"
