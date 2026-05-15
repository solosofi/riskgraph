#!/usr/bin/env bash
# browser-proxy.sh — Bridges WSL Chrome CDP to Docker containers
# Run in WSL after starting Chrome with --remote-debugging-port=9222

CHROME_PORT="${CHROME_PORT:-9222}"
PROXY_PORT="${PROXY_PORT:-9876}"

if ! curl -s http://127.0.0.1:$CHROME_PORT/json/version > /dev/null 2>&1; then
    echo "Starting headless Chrome..."
    chromium --remote-debugging-port=$CHROME_PORT --headless --no-sandbox --disable-gpu &
    sleep 3
fi

WS_URL=$(curl -s http://127.0.0.1:$CHROME_PORT/json/version | python3 -c "import sys,json; print(json.load(sys.stdin)['webSocketDebuggerUrl'])")
echo "Chrome CDP: $WS_URL"

if command -v socat &>/dev/null; then
    echo "Forwarding 0.0.0.0:$PROXY_PORT → 127.0.0.1:$CHROME_PORT"
    socat TCP-LISTEN:$PROXY_PORT,fork,reuseaddr TCP:127.0.0.1:$CHROME_PORT
else
    echo "Install socat: sudo apt install -y socat"
    exit 1
fi
