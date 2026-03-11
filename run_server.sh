#!/bin/bash
# ============================================================
#  MediScan AI Server — Start Server (Mac)
#  Usage: bash run_server.sh
# ============================================================

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║        MediScan AI Server — Starting...              ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

if [ ! -d "venv" ]; then
    echo "✗ Run setup first: bash setup_mac.sh"
    exit 1
fi

source venv/bin/activate

# Show IP addresses
echo "► Your Mac's IP addresses:"
ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print "  → " $2}'
echo ""
echo "  Use one of these in your Android app's BASE_URL"
echo "  Example: http://192.168.x.x:8000/"
echo ""

mkdir -p data/uploads data/results

echo "► Starting server on port 8000..."
echo "  Docs:   http://localhost:8000/docs"
echo "  Health: http://localhost:8000/health"
echo "  (Ctrl+C to stop)"
echo ""

python backend/fastapi_app.py
