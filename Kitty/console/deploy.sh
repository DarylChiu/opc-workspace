#!/bin/bash
# Deploy Gosh Console to Cloudflare Pages (static fallback)
set -e

SOURCE_DIR="/Users/zhaoyuzhao/WorkBuddy/Claw/console"
PROJECT_NAME="gosh-console"
WRANGLER="/Users/zhaoyuzhao/.workbuddy/binaries/node/workspace/node_modules/.bin/wrangler"

if [ ! -x "$WRANGLER" ]; then
  echo "Installing wrangler..."
  /Users/zhaoyuzhao/.workbuddy/binaries/node/versions/22.22.2/bin/npx wrangler --version
  WRANGLER="/Users/zhaoyuzhao/.workbuddy/binaries/node/versions/22.22.2/bin/npx wrangler"
fi

echo "Deploying Gosh Console to Cloudflare Pages..."
cd "$SOURCE_DIR"
$WRANGLER pages deploy . --project-name "$PROJECT_NAME" 2>&1

echo ""
echo "Deployment complete!"
echo "Primary (dynamic): http://localhost:8766"
echo "Fallback (static):  https://gosh-console.pages.dev"
