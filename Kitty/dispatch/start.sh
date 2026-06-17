#!/bin/bash
# Start Gosh Dispatch Server + Cloudflare Tunnel
# This script runs the Flask server AND exposes it via Cloudflare Tunnel

set -e

DISPATCH_DIR="/Users/zhaoyuzhao/WorkBuddy/Claw/dispatch"
URL_FILE="/Users/zhaoyuzhao/WorkBuddy/Claw/dispatch/tunnel_url.txt"
PYTHON="/Library/Frameworks/Python.framework/Versions/3.12/bin/python3"
PORT=8766

# Kill old instances
kill $(lsof -ti :$PORT) 2>/dev/null || true

echo "Starting Gosh Dispatch server..."

# Start Flask server
cd "$DISPATCH_DIR"
$PYTHON server.py &
FLASK_PID=$!
sleep 2

# Verify Flask is up
if ! curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/ | grep -q 200; then
  echo "ERROR: Flask server didn't start"
  exit 1
fi

echo "Flask server running on :$PORT"

# Start Cloudflare Tunnel (trycloudflare — free, no domain needed)
echo "Starting Cloudflare Tunnel..."
cloudflared tunnel --url http://localhost:$PORT > "$URL_FILE" 2>&1 &
TUNNEL_PID=$!

# Wait for the tunnel URL to appear
for i in {1..30}; do
  if grep -q "trycloudflare.com" "$URL_FILE" 2>/dev/null; then
    URL=$(grep -o 'https://[^ ]*trycloudflare\.com' "$URL_FILE" | head -1)
    echo ""
    echo "================================================"
    echo "  Dispatch 公网 URL:"
    echo "  $URL"
    echo "================================================"
    echo ""
    echo "手机打开这个链接即可远程下指令给 Agent。"
    echo "关闭此终端窗口 = 停止服务。"
    echo ""
    break
  fi
  sleep 1
done

# Cleanup on exit
cleanup() {
  echo "Shutting down..."
  kill $TUNNEL_PID 2>/dev/null
  kill $FLASK_PID 2>/dev/null
  rm -f "$URL_FILE"
}
trap cleanup EXIT

# Keep running
wait
