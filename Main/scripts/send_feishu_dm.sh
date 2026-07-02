#!/bin/bash
# 生活助手DM发送脚本 (LaunchAgent兼容版)
# 用法: send_feishu_dm.sh "消息内容"

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

MESSAGE="$1"

/opt/homebrew/bin/node /opt/homebrew/lib/node_modules/openclaw/dist/index.js message send \
  --channel feishu \
  --account default \
  --target user:ou_3bf0d4dcf7a80d6ddf15be5bd2f7ad4f \
  --message "$MESSAGE"
