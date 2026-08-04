#!/bin/bash
# 视频剪辑MVP · TOSHIBA EXT 硬盘看护
# 每10分钟检测：素材目录可读 → 标记OK；不可读 → 尝试挂载，仍失败 → 标记DEAD
# 状态文件: drive_status.txt (OK/DEAD + 时间戳)
# ⚠️ launchd 环境 PATH 极简，必须显式包含 /opt/homebrew/bin（timeout 是 GNU coreutils）

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
TIMEOUT="/opt/homebrew/bin/timeout"

MATERIAL="/Volumes/TOSHIBA EXT/Video/Raw Materials/Insta 360"
BASE="/Users/zhaoyuzhao/.openclaw/xiaofeng_workspace/video_editor_mvp"
MARKER="$BASE/drive_status.txt"
LOG="$BASE/drive_watchdog.log"
TS=$(date "+%Y-%m-%d %H:%M:%S")

# 可读性检测（间歇性卡死时重试3次再判定）
check_readable() {
    for i in 1 2 3; do
        if "$TIMEOUT" 8 ls "$MATERIAL" >/dev/null 2>&1; then
            return 0
        fi
        sleep 3
    done
    return 1
}

# 1. 直接可读？
if check_readable; then
    echo "$TS OK" > "$MARKER"
    echo "$TS OK readable" >> "$LOG"
    exit 0
fi

# 2. 不可读 → 找 TOSHIBA 分区节点（防止重插后节点变化）
NODE=$(diskutil list 2>/dev/null | grep "TOSHIBA EXT" | awk '{print $NF}' | head -1)

if [ -n "$NODE" ]; then
    # 设备在，但没挂载 → 尝试挂载
    if ! mount | grep -q "TOSHIBA EXT"; then
        diskutil mount "$NODE" >> "$LOG" 2>&1
        sleep 3
    fi
    if check_readable; then
        echo "$TS OK (remounted)" > "$MARKER"
        echo "$TS OK after remount ($NODE)" >> "$LOG"
        exit 0
    fi
    echo "$TS DEAD mounted-but-unreadable ($NODE)" > "$MARKER"
    echo "$TS DEAD mounted-unreadable ($NODE)" >> "$LOG"
else
    echo "$TS DEAD device-absent" > "$MARKER"
    echo "$TS DEAD device-absent" >> "$LOG"
fi
