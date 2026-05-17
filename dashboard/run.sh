#!/usr/bin/env bash
# Streamlit dashboard — port 8505
cd "$(dirname "$0")/.."
VENV=~/.hermes/hermes-agent/venv/bin

echo ""
echo "  Industry Monitor (Streamlit)"
echo "  Open: http://localhost:8505"
echo ""
echo "  若打不开，请改用静态看板："
echo "    ./dashboard/serve.sh"
echo "    -> http://localhost:8505/dashboard/static/index.html"
echo ""

if [ -x "$VENV/streamlit" ]; then
  exec "$VENV/streamlit" run dashboard/app.py \
    --server.port 8505 \
    --server.address 127.0.0.1 \
    --server.headless true \
    --browser.gatherUsageStats false
else
  exec "$VENV/python" -m streamlit run dashboard/app.py \
    --server.port 8505 \
    --server.address 127.0.0.1 \
    --server.headless true \
    --browser.gatherUsageStats false
fi
