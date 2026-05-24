#!/bin/bash
# auto_deploy.sh — 周一采集 + 流水线 + git push → Streamlit Cloud 自动部署
set -euo pipefail

ROOT="/home/xxxsuli/industry-monitor"
VENV_PYTHON="/home/xxxsuli/.hermes/hermes-agent/venv/bin/python"
LOG="$ROOT/data/raw/_auto_deploy_log.txt"

cd "$ROOT"

echo "=== auto_deploy $(date -Iseconds) ===" | tee "$LOG"

# Step 1: Collect + Pipeline
bash "$ROOT/scripts/daily_update.sh" 2>&1 | tee -a "$LOG"

# Step 2: Git push (Streamlit Cloud auto-deploys on push)
echo "--- Git Push ---" | tee -a "$LOG"
git add -A 2>&1 | tee -a "$LOG"
git commit -m "auto: weekly data update $(date +%Y-%m-%d)" 2>&1 | tee -a "$LOG" || true
git push 2>&1 | tee -a "$LOG"

echo "=== Deploy Done $(date -Iseconds) ===" | tee -a "$LOG"
