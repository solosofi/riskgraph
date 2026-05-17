#!/usr/bin/env bash
# real-chrome-bridge.sh — expose the user's NORMAL Chrome profile to Hermes/Docker via CDP.
# This intentionally avoids Selenium and avoids a separate "controlled by automated software" profile.
# Run from WSL. It launches Windows Chrome with your real Default profile and remote debugging.
set -euo pipefail

CHROME_PORT="${CHROME_PORT:-9222}"
PROXY_PORT="${PROXY_PORT:-9876}"
LOG_DIR="${LOG_DIR:-$HOME/.cache/hermes-browser}"
mkdir -p "$LOG_DIR"
CHROME_LOG="$LOG_DIR/chrome-cdp.log"
SOCAT_LOG="$LOG_DIR/socat-cdp.log"

# Kill only old bridges/debug-launches, not arbitrary normal Chrome unless needed.
pkill -f "socat TCP-LISTEN:${PROXY_PORT}" 2>/dev/null || true

find_windows_chrome() {
  for p in \
    "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe" \
    "/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe" \
    "/mnt/c/Users/$USER/AppData/Local/Google/Chrome/Application/chrome.exe" \
    "/mnt/c/Program Files/Microsoft/Edge/Application/msedge.exe"; do
    [ -x "$p" ] && { echo "$p"; return 0; }
  done
  command -v chrome.exe 2>/dev/null && return 0
  command -v google-chrome 2>/dev/null && return 0
  command -v chromium 2>/dev/null && return 0
  return 1
}

CHROME_BIN="$(find_windows_chrome || true)"
if [ -z "$CHROME_BIN" ]; then
  echo "No Chrome/Edge binary found." >&2
  exit 1
fi

# If no CDP endpoint is live, launch real Chrome/Edge with remote debugging.
# IMPORTANT: no --user-data-dir. This uses your real logged-in profile.
if ! curl -fsS "http://127.0.0.1:${CHROME_PORT}/json/version" >/dev/null 2>&1; then
  echo "Launching real Chrome with CDP on :${CHROME_PORT} using: $CHROME_BIN"
  "$CHROME_BIN" \
    --remote-debugging-port="${CHROME_PORT}" \
    --remote-allow-origins='*' \
    --no-first-run \
    --no-default-browser-check \
    about:blank >"$CHROME_LOG" 2>&1 &
  for i in $(seq 1 20); do
    curl -fsS "http://127.0.0.1:${CHROME_PORT}/json/version" >/dev/null 2>&1 && break
    sleep 1
  done
fi

if ! curl -fsS "http://127.0.0.1:${CHROME_PORT}/json/version" >/dev/null 2>&1; then
  echo "CDP did not start. If Chrome was already running, fully exit Chrome from the tray/taskbar and rerun this script." >&2
  echo "Chrome log: $CHROME_LOG" >&2
  exit 2
fi

if ! command -v socat >/dev/null 2>&1; then
  echo "socat missing. Install once: sudo apt install -y socat" >&2
  exit 3
fi

# Bridge for Docker containers. Keep process in background and print concrete endpoint.
nohup socat TCP-LISTEN:"${PROXY_PORT}",bind=0.0.0.0,fork,reuseaddr TCP:127.0.0.1:"${CHROME_PORT}" >"$SOCAT_LOG" 2>&1 &
sleep 1

VERSION="$(curl -fsS "http://127.0.0.1:${PROXY_PORT}/json/version")"
WS_URL="$(python3 - <<'PY' <<<"$VERSION"
import json,sys
p=json.load(sys.stdin)
print(p.get('webSocketDebuggerUrl','').replace('127.0.0.1:9222','host.docker.internal:9876'))
PY
)"

echo "OK real Chrome CDP bridge ready"
echo "Local discovery:  http://127.0.0.1:${PROXY_PORT}/json/version"
echo "Docker discovery: http://host.docker.internal:${PROXY_PORT}/json/version"
echo "WebSocket:        ${WS_URL}"
echo "Logs:             $CHROME_LOG ; $SOCAT_LOG"
