#!/usr/bin/env bash
# ───── CodeSync launcher for macOS / Linux ─────
cd "$(dirname "$0")"
echo
echo "=== Installing dependencies (first run only) ==="
python3 -m pip install --quiet -r requirements.txt || {
    echo "[ERROR] Failed to install dependencies. Install Python 3.9+ first."
    exit 1
}
echo
echo "=== Starting CodeSync ==="
echo "Open http://localhost:5000 in your browser"
echo "Press Ctrl+C to stop the server"
echo
python3 server.py
