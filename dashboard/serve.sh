#!/usr/bin/env bash
# Streamlit dashboard — dynamic with live TRL + auto conclusion :8505
# Open: http://localhost:8505
set -euo pipefail
cd "$(dirname "$0")/.."

VENV_PYTHON="$HOME/.hermes/hermes-agent/venv/bin/python"

echo ""
echo "  📡 Industry Monitor v6 (Streamlit)"
echo "  http://localhost:8505"
echo ""

exec "$VENV_PYTHON" -m streamlit run dashboard/app.py \
  --server.port 8505 \
  --server.headless true \
  --server.address 0.0.0.0
