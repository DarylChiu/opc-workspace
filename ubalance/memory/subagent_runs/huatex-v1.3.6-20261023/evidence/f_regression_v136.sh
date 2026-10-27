#!/bin/bash
# v1.3.6 回归 —— 脱离 dev 树，纯 HTTP 驱动包内 app（重点：进出口材料 Outcome2 的 PDF+Excel 成对）
set -u
WS=/Users/zhaoyuzhao/.openclaw/workspace-balance
EV=$WS/memory/subagent_runs/huatex-v1.3.6-20261023/evidence
PKG=/tmp/hv136/unzip/HUATEX-Tools          # 已解压的交付包产物（唯一被测对象）
DL=/tmp/hv136/dl
LBASE=$WS/work/loan-materials-2025-12/out/v2.8d-2025_12-20261014_1526
LIN=$WS/work/loan-materials-2025-12/in/L1-成品采购入库补单测试20条.xlsx
SRC="/Volumes/TOSHIBA EXT/HUATEX进出口材料"
CMP=$WS/portable/tools/compare_xlsx.py

mkdir -p $EV $DL
exec > >(tee $EV/regression.log) 2>&1
echo "=== v1.3.6 回归开始 $(date '+%F %T') ==="
echo "被测包 = $PKG"

lsof -ti :8000 >/dev/null 2>&1 && { echo "[!] 8000 被占用，先停旧服务"; lsof -ti :8000 | xargs kill -9; sleep 1; }

cp $WS/portable/config.regression-2025_12.yaml $PKG/config.regression-2025_12.yaml
cp $WS/memory/subagent_runs/huatex-v1.3.4-20261016/evidence/pkg_drive.py $DL/

cd $PKG || exit 1
python3 tools/preflight.py --selftest > $EV/pkg_test_preflight.log 2>&1
echo "preflight selftest rc=$? → $EV/pkg_test_preflight.log"

nohup python3 app/server.py > $EV/pkg_test_server.log 2>&1 &
SRV=$!; echo $SRV > /tmp/hv136/server.pid
sleep 5
cd $DL
python3 pkg_drive.py state > $EV/api_state.json 2>&1 && echo "[OK] 服务已起 pid=$SRV" || { echo "[x] 服务未起"; cat $EV/pkg_test_server.log; exit 1; }
python3 pkg_drive.py save-root "$SRC" > $EV/page0_save_source_root.txt 2>&1
cat $EV/page0_save_source_root.txt

echo "=== 进出口材料运行（约 5-8 分钟）==="
python3 pkg_drive.py run loan "$LIN" --params "{\"override\":\"$PKG/config.regression-2025_12.yaml\",\"tag\":\"2025_12\",\"months\":[[\"2025\",\"THÁNG 12\"],[\"2026\",\"THÁNG 01\"]],\"batch_dir\":\"loan-materials-2025-12\",\"source_root\":\"$SRC\"}" > $EV/loan_run.log 2>&1
echo "loan_run rc=$?"
LJOB=$(grep -o 'RESULT job=[^ ]*' $EV/loan_run.log | cut -d= -f2)
LSTATUS=$(grep -o 'RESULT job=[^ ]* status=[^ ]*' $EV/loan_run.log | awk '{print $3}')
echo "Loan job=$LJOB status=$LSTATUS"
echo "$LSTATUS" > $EV/loan_status.txt
tail -40 $EV/loan_run.log

LONE=$(find $PKG/runs/$LJOB/out -name 'Outcome1-*.xlsx' 2>/dev/null | head -1)
LOUT=$(dirname "$LONE")
echo "Loan out=$LOUT"
echo "$LOUT" > $EV/loan_out_dir.txt

# ── Outcome1 对拍（与 10-14 基线）──
if [ -n "$LONE" ]; then
  python3 "$CMP" --base "$(ls $LBASE/Outcome1-*.xlsx | head -1)" --new "$LONE" > $EV/loan_outcome1_diff.txt 2>&1
  echo "Outcome1 对比退出码=$?" >> $EV/loan_outcome1_diff.txt
  cat $EV/loan_outcome1_diff.txt
fi

# ── Outcome2 逐票 PDF+Excel 成对核查 ──
if [ -n "$LOUT" ]; then
  python3 - "$LOUT/Outcome2" "$LBASE/Outcome2" > $EV/loan_outcome2_pairs.txt 2>&1 <<'PY'
import os, sys, re
new = sys.argv[1]; base = sys.argv[2]
def scan(root):
    out = {}
    for t in sorted(os.listdir(root)):
        d = os.path.join(root, t)
        if not os.path.isdir(d): continue
        fs = sorted(x for x in os.listdir(d) if not x.startswith('._'))
        pdf = [x for x in fs if re.search(r'清关资料中英文明细.*\.pdf$', x, re.I)]
        xls = [x for x in fs if re.search(r'清关资料中英文明细.*\.xls[xm]?$', x, re.I)]
        out[t] = (fs, pdf, xls)
    return out
n = scan(new); b = scan(base)
print('新产出票数 = %d ；基线票数 = %d' % (len(n), len(b)))
print()
pair_ok = []; pair_bad = []; empty = []
for t in sorted(n, key=lambda x: (len(x), x)):
    fs, pdf, xls = n[t]
    if not fs:
        empty.append(t); print('空票   %-22s  (源盘无目录/无材料)' % t); continue
    if pdf and xls:
        pair_ok.append(t); flag = 'PAIR ✅'
    else:
        pair_bad.append(t); flag = 'PAIR ❌ pdf=%d xls=%d' % (len(pdf), len(xls))
    print('%-22s %-28s' % (t, flag))
    for f in fs: print('        - %s' % f)
print()
print('成对(含PDF+Excel) = %d ；只缺一边 = %d ；空票 = %d' % (len(pair_ok), len(pair_bad), len(empty)))
if pair_bad: print('不达标票:', pair_bad)
if empty: print('空票:', empty)
print()
print('基线各票文件数（对比参考）:')
for t in sorted(b): print('   %-22s %d 个文件' % (t, len(b[t][0])))
PY
  cat $EV/loan_outcome2_pairs.txt
  python3 pkg_drive.py download $LJOB Outcome2.zip $DL/Outcome2.zip > $EV/loan_download.txt 2>&1
  cat $EV/loan_download.txt
fi

# ── 收尾 ──
kill $SRV 2>/dev/null; sleep 1; pkill -f "app/server.py" 2>/dev/null
lsof -ti :8000 >/dev/null 2>&1 && lsof -ti :8000 | xargs kill -9 2>/dev/null
echo "server stopped: $(lsof -ti :8000 | wc -l | tr -d ' ') listeners left" | tee $EV/server_stop.txt
echo "=== v1.3.6 回归结束 $(date '+%F %T') ==="
