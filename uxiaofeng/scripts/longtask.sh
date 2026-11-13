#!/usr/bin/env bash
# longtask.sh — 长线任务状态机（跨 session / 跨 compaction 抗遗忘）
# 每次一个"回合"读写 state 文件，context 只装当前 Step，不装全历史。
#
# 用法:
#   longtask.sh init <slug> "<目标>"
#   longtask.sh step <slug> "<步骤名>"        # 设为当前步骤（in_progress）
#   longtask.sh log <slug> "<笔记>"           # 追加笔记/中间产物/路径
#   longtask.sh done <slug> ["<备注>"]        # 当前步骤完成，推进到下一条 pending
#   longtask.sh add <slug> "<步骤名>"         # 追加 pending 步骤
#   longtask.sh status [slug]                 # 查看（无参=列出所有）
#   longtask.sh block <slug> "<原因>"         # 标记阻塞
#
# 状态目录: memory/longtask/<slug>.md
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIR="$ROOT/memory/longtask"
mkdir -p "$DIR"
cmd="${1:-status}"; slug="${2:-}"; arg3="${3:-}"
F="$DIR/$slug.md"

now(){ date '+%Y-%m-%d %H:%M'; }

case "$cmd" in
  init)
    [ -f "$F" ] && { echo "已存在: $F"; exit 0; }
    cat > "$F" <<EOF
# 长线任务: $slug

- 目标: $arg3
- 创建: $(now)
- 更新: $(now)
- 状态: running

## 步骤
- [ ] 步骤1（待填写）

## 进度日志
EOF
    echo "已创建 $F" ;;
  step)
    python3 - "$F" "$arg3" <<'PY'
import sys,re,datetime
p,step=sys.argv[1],sys.argv[2]
lines=open(p).read().split("\n")
out=[]
in_steps=False
for ln in lines:
    if ln.startswith("## 步骤"): in_steps=True; out.append(ln); continue
    if ln.startswith("## "): in_steps=False; out.append(ln); continue
    if in_steps and ln.startswith("- [>] ") and ln[6:]!=step:
        out.append("- [ ] "+ln[6:]); continue
    if in_steps and ln==f"- [ ] {step}":
        out.append(f"- [>] {step}"); continue
    if ln.startswith("- 更新: "):
        out.append("- 更新: "+datetime.datetime.now().strftime('%Y-%m-%d %H:%M')); continue
    out.append(ln)
s="\n".join(out)
if f"- [>] {step}" not in s:
    s=s.replace("## 步骤\n", f"## 步骤\n- [>] {step}\n",1)
s=re.sub(r"- \[ \] 步骤1（待填写）\n?","",s)
open(p,"w").write(s)
PY
    echo "当前步骤 → $arg3" ;;
  add)
    python3 - "$F" "$arg3" <<'PY'
import sys
p,step=sys.argv[1],sys.argv[2]
s=open(p).read()
head,sep,tail=s.partition("## 步骤")
block,sep2,rest=tail.partition("## 进度日志")
block=block.replace("- [ ] 步骤1（待填写）\n","")
block=block.rstrip("\n")+"\n"+f"- [ ] {step}\n\n"
p=sys.argv[1]
open(p,"w").write(head+sep+block+sep2+rest)
PY
    echo "追加步骤: $arg3" ;;
  log)
    printf '\n- %s %s\n' "$(now)" "$arg3" >> "$F"
    echo "已记录" ;;
  done)
    python3 - "$F" "$arg3" <<'PY'
import sys,re,datetime
p,note=sys.argv[1],sys.argv[2]
s=open(p).read()
s=re.sub(r"- \[>\] (.*)",lambda m:f"- [x] {m.group(1)}",s,count=1)
s=re.sub(r"- \[ \] (.*)",lambda m:f"- [>] {m.group(1)}",s,count=1)
s=re.sub(r"^- 更新: .*$","- 更新: "+datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),s,flags=re.M)
if note: s=s.rstrip()+f"\n- {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} [done] {note}\n"
if "- [>]" not in s and "- [ ]" not in s:
    s=re.sub(r"^- 状态: .*$","- 状态: done ✅",s,flags=re.M)
open(p,"w").write(s)
PY
    echo "推进完成" ;;
  block)
    python3 - "$F" "$arg3" <<'PY'
import sys,re
p,why=sys.argv[1],sys.argv[2]
s=open(p).read()
s=re.sub(r"^- 状态: .*$","- 状态: blocked ⛔ ("+why.replace('\\','')+")",s,flags=re.M)
open(p,"w").write(s)
PY
    echo "已标记阻塞: $arg3" ;;
  status)
    if [ -z "$slug" ]; then
      for f in "$DIR"/*.md; do [ -e "$f" ] || continue
        st=$(grep -m1 '^- 状态:' "$f" | sed 's/^- 状态: //')
        cur=$(grep -m1 '^- \[>\]' "$f" | sed 's/^- \[>\] //' || true)
        printf '%-28s %-12s %s\n' "$(basename "$f" .md)" "$st" "${cur}"
      done
    else
      cat "$F"
    fi ;;
  *) echo "unknown: $cmd"; exit 1 ;;
esac
