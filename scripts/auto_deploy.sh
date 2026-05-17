#!/bin/bash
# auto_deploy.sh — 每日采集+流水线 → 提交 → 推送 → Streamlit Cloud 自动部署
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PYTHON="$HOME/.hermes/hermes-agent/venv/bin/python"
cd "$ROOT"

echo "=== auto_deploy $(date -Iseconds) ==="

# Step 1: Collect + Pipeline
echo "--- Collect ---"
"$VENV_PYTHON" collectors/run_all.py 2>&1 || echo "WARNING: collectors had errors"

echo "--- Pipeline ---"
"$VENV_PYTHON" processors/run_pipeline.py 2>&1 || echo "WARNING: pipeline had errors"

# Step 2: Commit data files
git add data/processed/ data/models/causal_chains.json

if git diff --cached --quiet; then
    echo "No data changes, skipping commit"
    exit 0
fi

git commit -m "data: daily auto-update $(date +%Y-%m-%d)"
git push origin main
echo "=== Done: pushed to GitHub, Streamlit Cloud will redeploy ==="
