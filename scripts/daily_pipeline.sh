#!/bin/bash
# daily_pipeline.sh — 每日运行流水线（分类→TRL→告警）
set -euo pipefail

ROOT="/home/xxxsuli/industry-monitor"
VENV_PYTHON="/home/xxxsuli/.hermes/hermes-agent/venv/bin/python"
LOG="$ROOT/data/processed/_pipeline_log.txt"

cd "$ROOT"

echo "=== $(date -Iseconds) ===" | tee "$LOG"

"$VENV_PYTHON" processors/run_pipeline.py 2>&1 | tee -a "$LOG"

echo "=== Done $(date -Iseconds) ===" | tee -a "$LOG"
