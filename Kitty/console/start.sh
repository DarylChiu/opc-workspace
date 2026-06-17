#!/bin/bash
# Gosh Console — Unified remote control center
# Start: Flask backend (8766) + Cloudflare Tunnel (public URL)
# Kill: Close this terminal window

set -e

CONSOLE="/Users/zhaoyuzhao/WorkBuddy/Claw/console"
PYTHON="/Library/Frameworks/Python.framework/Versions/3.12/bin/python3"
PORT=8766
URL_FILE="$CONSOLE/tunnel_url.txt"

# Clean old instances
kill $(lsof -ti :$PORT) 2>/dev/null || true
rm -f "$URL_FILE"

echo "════════════════════════════════════════════"
echo "  Gosh Console"
echo "════════════════════════════════════════════"

# Start Flask
cd "$CONSOLE"
$PYTHON server.py &
FLASK_PID=$!
sleep 2

if ! curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/ | grep -q 200; then
  echo "✕ Flask server failed to start"
  exit 1
fi
echo "✓ Local: http://localhost:$PORT"

# Public tunnel — try localtunnel first (zero auth), fallback to cloudflared
LT="/Users/zhaoyuzhao/.workbuddy/binaries/node/workspace/node_modules/.bin/lt"
CFT="cloudflared"

if [ -x "$LT" ]; then
  echo "  Starting localtunnel..."
  $LT --port $PORT > "$URL_FILE" 2>&1 &
  TUNNEL_PID=$!
  for i in {1..20}; do
    if grep -q "your url is:" "$URL_FILE" 2>/dev/null; then
      URL=$(grep -o 'https://[^ ]*loca\.lt' "$URL_FILE" | head -1)
      echo "  Public: $URL"
      break
    fi
    sleep 1
  done
elif command -v $CFT &>/dev/null && [ -f "$HOME/.cloudflared/cert.pem" ]; then
  echo "  Starting Cloudflare Tunnel..."
  $CFT tunnel --url http://localhost:$PORT > "$URL_FILE" 2>&1 &
  TUNNEL_PID=$!
  for i in {1..30}; do
    if grep -q "trycloudflare.com" "$URL_FILE" 2>/dev/null; then
      URL=$(grep -o 'https://[^ ]*trycloudflare\.com' "$URL_FILE" | head -1)
      echo "  Public: $URL"
      break
    fi
    sleep 1
  done
else
  echo "  ℹ No tunnel available. Run: npm install -g localtunnel"
fi

echo "════════════════════════════════════════════"
echo "  Close this window to stop the server."
echo "════════════════════════════════════════════"

cleanup() {
  echo ""
  echo "Shutting down..."
  kill $TUNNEL_PID 2>/dev/null
  kill $FLASK_PID 2>/dev/null
  rm -f "$URL_FILE"
}
trap cleanup EXIT
wait
