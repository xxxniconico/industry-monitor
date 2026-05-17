#!/usr/bin/env bash
# Static HTML dashboard — works without Streamlit (recommended on WSL)
# Open: http://localhost:8505/dashboard/static/index.html
cd "$(dirname "$0")/.."
echo ""
echo "  Industry Monitor (static)"
echo "  Open in browser:"
echo "    http://localhost:8505/dashboard/static/index.html"
echo ""
echo "  Press Ctrl+C to stop."
echo ""
exec python3 -m http.server 8505 --bind 127.0.0.1
