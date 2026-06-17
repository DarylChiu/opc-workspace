#!/bin/bash
# Cloudflare Pages Deployment for Gosh Dashboard

PROJECT_NAME="gosh-dashboard"
SOURCE_DIR="/Users/zhaoyuzhao/WorkBuddy/Claw/dashboard"
WRANGLER="/Users/zhaoyuzhao/.workbuddy/binaries/node/versions/22.22.2/bin/wrangler"

echo "Deploying Gosh Dashboard to Cloudflare Pages..."
echo ""

# Check login status
$WRANGLER whoami 2>/dev/null || {
  echo "Not logged in. Run: $WRANGLER login"
  echo "Then re-run this script."
  exit 1
}

# Deploy static files
$WRANGLER pages deploy "$SOURCE_DIR" --project-name "$PROJECT_NAME" 2>&1

echo ""
echo "Deployment complete!"
echo "Your dashboard will be at: https://${PROJECT_NAME}.pages.dev"
echo ""
echo "Note: Cloudflare Pages serves static files only."
echo "For the dynamic Flask backend, use local http://localhost:8765"
