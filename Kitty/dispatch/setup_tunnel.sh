#!/bin/bash
# Setup Cloudflare Tunnel for Gosh Dispatch
# Run this ONCE after wrangler login is done

set -e

CREDS_FILE="/Users/zhaoyuzhao/.cloudflared/cert.pem"
TUNNEL_NAME="gosh-dispatch"
CONFIG_DIR="/Users/zhaoyuzhao/.cloudflared"
mkdir -p "$CONFIG_DIR"

# Check if already logged in
if [ ! -f "$CREDS_FILE" ]; then
  echo "Authenticating with Cloudflare..."
  cloudflared tunnel login
  echo ""
fi

# Create tunnel (idempotent)
if ! cloudflared tunnel list 2>/dev/null | grep -q "$TUNNEL_NAME"; then
  echo "Creating tunnel: $TUNNEL_NAME"
  cloudflared tunnel create "$TUNNEL_NAME"
else
  echo "Tunnel $TUNNEL_NAME already exists"
fi

TUNNEL_ID=$(cloudflared tunnel list -o json 2>/dev/null | python3 -c "
import json,sys
data = json.load(sys.stdin)
for t in data:
    if t.get('name') == '$TUNNEL_NAME':
        print(t['id'])
        break
")

if [ -z "$TUNNEL_ID" ]; then
  echo "ERROR: Could not find tunnel ID"
  exit 1
fi

# Write config
cat > "$CONFIG_DIR/config.yml" << ENDCONFIG
tunnel: $TUNNEL_ID
credentials-file: $CONFIG_DIR/${TUNNEL_ID}.json

ingress:
  - hostname: dispatch.gosh.yourdomain.com
    service: http://localhost:8766
  - service: http_status:404
ENDCONFIG

# Write DNS record info
echo ""
echo "================================================"
echo "Tunnel created: $TUNNEL_ID"
echo ""
echo "Next step — route a public hostname to this tunnel."
echo "You need a Cloudflare-managed domain for a custom hostname."
echo ""
echo "For a FREE trycloudflare.com URL (no domain needed), run:"
echo "  cloudflared tunnel --url http://localhost:8766"
echo "================================================"
