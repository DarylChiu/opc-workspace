#!/bin/bash
# OPC Dashboard — Start / Stop / Restart / Status
set -e

PORT=8765
DIR="$(cd "$(dirname "$0")" && pwd)"
PIDFILE="$DIR/.pid"
LOGFILE="$DIR/server.log"

start() {
  if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
    echo "OPC Dashboard is already running (PID $(cat $PIDFILE))"
    return 1
  fi
  echo "Starting OPC Dashboard on port $PORT..."
  cd "$DIR"
  nohup node server.js > "$LOGFILE" 2>&1 &
  echo $! > "$PIDFILE"
  sleep 1
  if kill -0 $(cat "$PIDFILE") 2>/dev/null; then
    echo "✅ Started (PID $(cat $PIDFILE)) → http://localhost:$PORT"
  else
    echo "❌ Failed to start. Check $LOGFILE"
    rm -f "$PIDFILE"
    return 1
  fi
}

stop() {
  if [ ! -f "$PIDFILE" ]; then
    echo "OPC Dashboard is not running"
    return 0
  fi
  PID=$(cat "$PIDFILE")
  if kill -0 "$PID" 2>/dev/null; then
    echo "Stopping OPC Dashboard (PID $PID)..."
    kill "$PID"
    for i in {1..10}; do
      if ! kill -0 "$PID" 2>/dev/null; then break; fi
      sleep 0.5
    done
    if kill -0 "$PID" 2>/dev/null; then
      echo "Force killing..."
      kill -9 "$PID" 2>/dev/null || true
    fi
    echo "✅ Stopped"
  fi
  rm -f "$PIDFILE"
}

restart() {
  stop
  sleep 1
  start
}

status() {
  if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
    PID=$(cat "$PIDFILE")
    echo "✅ OPC Dashboard running (PID $PID)"
    echo "   Port: $PORT"
    echo "   URL:  http://localhost:$PORT"
    lsof -i ":$PORT" 2>/dev/null | tail -1
  else
    echo "❌ OPC Dashboard not running"
    rm -f "$PIDFILE"
  fi
}

logs() {
  if [ -f "$LOGFILE" ]; then
    tail ${1:-20} "$LOGFILE"
  else
    echo "No log file found"
  fi
}

# Ngrok public URL
ngrok_start() {
  if ! command -v ngrok &>/dev/null; then
    echo "❌ ngrok not installed. Install: brew install ngrok"
    return 1
  fi
  echo "Starting ngrok tunnel to port $PORT..."
  ngrok http $PORT --log=stdout > "$DIR/ngrok.log" 2>&1 &
  NGPID=$!
  echo $NGPID > "$DIR/.ngrok_pid"
  sleep 3
  # Get the public URL
  PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin)['tunnels'][0]['public_url'])" 2>/dev/null)
  if [ -n "$PUBLIC_URL" ]; then
    echo "✅ Ngrok tunnel: $PUBLIC_URL"
  else
    echo "⚠️  Ngrok started but couldn't get URL. Check $DIR/ngrok.log"
  fi
}

ngrok_stop() {
  if [ -f "$DIR/.ngrok_pid" ]; then
    kill $(cat "$DIR/.ngrok_pid") 2>/dev/null || true
    rm -f "$DIR/.ngrok_pid"
    echo "✅ Ngrok stopped"
  fi
}

# Localtunnel — dedicated subdomain, no account needed, avoids ngrok free-tier limit
lt_start() {
  if ! command -v lt &>/dev/null; then
    echo "❌ localtunnel not installed. Install: npm i -g localtunnel"
    return 1
  fi
  lt_stop
  echo "Starting localtunnel to port $PORT..."
  nohup lt --port $PORT --subdomain opc-dashboard-daryl > "$DIR/lt.log" 2>&1 &
  LTPID=$!
  echo $LTPID > "$DIR/.lt_pid"
  sleep 3
  if [ -f "$DIR/lt.log" ]; then
    URL=$(grep -o 'https://[^ ]*\.loca\.lt' "$DIR/lt.log" 2>/dev/null | head -1)
    if [ -n "$URL" ]; then
      echo "✅ Localtunnel: $URL"
    else
      echo "⚠️  Localtunnel started but couldn't get URL. Check $DIR/lt.log"
    fi
  fi
}

lt_stop() {
  if [ -f "$DIR/.lt_pid" ]; then
    kill $(cat "$DIR/.lt_pid") 2>/dev/null || true
    rm -f "$DIR/.lt_pid"
    echo "✅ Localtunnel stopped"
  fi
}

case "${1:-start}" in
  start)   start ;;
  stop)    stop ;;
  restart) restart ;;
  status)  status ;;
  logs)    logs "${2:-20}" ;;
  ngrok)   ngrok_start ;;
  ngrok-stop) ngrok_stop ;;
  lt)      lt_start ;;
  lt-stop) lt_stop ;;
  cf)      cf_start ;;
  cf-stop) cf_stop ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|logs|ngrok|ngrok-stop|lt|lt-stop|cf|cf-stop}"
    exit 1
    ;;
esac

# Cloudflare Tunnel — free, no account, reliable
cf_start() {
  if ! command -v cloudflared &>/dev/null; then
    echo "❌ cloudflared not installed. Install: brew install cloudflare/cloudflare/cloudflared"
    return 1
  fi
  cf_stop
  echo "Starting Cloudflare Tunnel to port $PORT..."
  nohup cloudflared tunnel --url "http://localhost:$PORT" > "$DIR/cf.log" 2>&1 &
  CFPID=$!
  echo $CFPID > "$DIR/.cf_pid"
  sleep 5
  if [ -f "$DIR/cf.log" ]; then
    URL=$(grep -o 'https://[^ ]*\.trycloudflare\.com' "$DIR/cf.log" 2>/dev/null | head -1)
    if [ -n "$URL" ]; then
      echo "✅ Cloudflare Tunnel: $URL"
    else
      echo "⚠️  Cloudflared started but couldn't get URL. Check $DIR/cf.log"
    fi
  fi
}

cf_stop() {
  if [ -f "$DIR/.cf_pid" ]; then
    kill $(cat "$DIR/.cf_pid") 2>/dev/null || true
    rm -f "$DIR/.cf_pid"
    echo "✅ Cloudflared stopped"
  fi
}
