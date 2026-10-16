#!/bin/bash
# v1.3.4 冒烟回归 —— 脱离 dev 树，纯 HTTP 驱动；Payment + Loan 双流程
set -u
WS=/Users/zhaoyuzhao/.openclaw/workspace-balance
EV=$WS/memory/subagent_runs/huatex-v1.3.4-20261016/evidence
PKG=/tmp/huatex-v134-test
DL=$PKG/dl
PBASE=$WS/work/payprep-20261013/out
PIN=$WS/work/payprep-20261013/in
LBASE=$WS/work/loan-materials-2025-12/out/v2.8d-2025_12-20261014_1526
LIN=$WS/work/loan-materials-2025-12/in/L1-成品采购入库补单测试20条.xlsx
CMP=$WS/portable/tools/compare_xlsx.py

exec > >(tee $EV/regression.log) 2>&1
echo "=== v1.3.4 回归开始 $(date '+%F %T') ==="

lsof -ti :8000 >/dev/null 2>&1 && { echo "[!] 8000 被占用，先停旧服务"; lsof -ti :8000 | xargs kill -9; sleep 1; }
mkdir -p $DL
cp $WS/portable/config.regression-2025_12.yaml $PKG/HUATEX-Tools/config.regression-2025_12.yaml
cd $PKG/HUATEX-Tools || exit 1
python3 tools/preflight.py --selftest > $EV/pkg_test_preflight.log 2>&1
echo "preflight rc=$?" >> $EV/pkg_test_preflight.log
echo "[OK] 包内自检 → $EV/pkg_test_preflight.log"

nohup python3 app/server.py > $PKG/server.log 2>&1 &
SRV=$!; echo $SRV > $PKG/server.pid
sleep 4
cp $EV/pkg_drive.py $DL/
cd $DL
python3 pkg_drive.py state > $EV/api_state.json 2>&1 && echo "[OK] 服务已起 pid=$SRV" || { echo "[x] 服务未起"; cat $PKG/server.log; exit 1; }
python3 pkg_drive.py save-root "/Volumes/TOSHIBA EXT/HUATEX进出口材料" > $EV/page0_save_source_root.txt 2>&1
cat $EV/page0_save_source_root.txt

# ─────────── Payment（10-13 批次 4 文件） ───────────
echo "=== Payment 运行 ==="
python3 pkg_drive.py run payment "$PIN/10-12华特明细待确认.xlsx" \
    "$PIN/voucher-a1013.zip" "$PIN/voucher-b1013.zip" "$PIN/voucher-c1013.zip" \
    --params '{"date":"20261013"}' > $EV/payment_run.log 2>&1
PJOB=$(grep -o 'RESULT job=[^ ]*' $EV/payment_run.log | cut -d= -f2)
PSTATUS=$(grep -o 'RESULT job=[^ ]* status=[^ ]*' $EV/payment_run.log | awk '{print $3}')
echo "Payment job=$PJOB status=$PSTATUS"
POUT=$PKG/HUATEX-Tools/runs/$PJOB/out
ls -la "$POUT" 2>/dev/null

: > $EV/payment_diff.txt
for f in "Payment request to Bank-20261013.xlsx" "Payment recon ledger-20261013.xlsx" "Payment 待人工核清单-20261013.xlsx"; do
  echo "################ $f" >> $EV/payment_diff.txt
  python3 "$CMP" --base "$PBASE/$f" --new "$POUT/$f" >> $EV/payment_diff.txt 2>&1
  echo "退出码=$?" >> $EV/payment_diff.txt
done
grep -c "差异总数 = 0" $EV/payment_diff.txt > $EV/payment_diff_pass.txt
echo "差异0计数=$(cat $EV/payment_diff_pass.txt)"
echo "md5(recon.txt) base=$(md5 -q "$PBASE/Payment request to Bank-20261013.xlsx.recon.txt") new=$(md5 -q "$POUT/Payment request to Bank-20261013.xlsx.recon.txt")" | tee $EV/payment_recon_txt_md5.txt
# 关键日志行
grep -o "\[jobs\] 待人工核清单 rc=[0-9]*" $EV/payment_run.log | tail -3 | tee $EV/payment_mr_rc.txt
cp $PKG/HUATEX-Tools/runs/$PJOB/job.json $EV/payment_job.json 2>/dev/null

# ─────────── Step4b：用包内 runs 自产的 recon.json 复跑编码实测 ───────────
PKG_RECON=$(ls "$POUT"/*.recon.json 2>/dev/null | head -1)
if [ -n "$PKG_RECON" ]; then
  echo "=== 4b) 包内 runs 自产 recon.json 的编码实测：$PKG_RECON"
  rm -f /tmp/mr_pkg.xlsx
  env PYTHONUTF8=0 PYTHONCOERCECLOCALE=0 LC_ALL=C PYTHONIOENCODING=utf-8 \
    python3 "$PKG/HUATEX-Tools/workflows/payprep/manual_review.py" \
    --recon-json "$PKG_RECON" --detail "$PIN/10-12华特明细待确认.xlsx" \
    --out /tmp/mr_pkg.xlsx --date 20261013 >> $EV/winenc_manual_review.txt 2>&1
  echo "RC_PKG_RECON=$?" | tee -a $EV/winenc_manual_review.txt
  ls -la /tmp/mr_pkg.xlsx 2>&1 | tee -a $EV/winenc_manual_review.txt
fi

# ─────────── Loan（2025_12 等价 override，S4.2 同口径） ───────────
echo "=== Loan 运行（约 5 分钟）==="
python3 pkg_drive.py run loan "$LIN" --params "{\"override\":\"$PKG/HUATEX-Tools/config.regression-2025_12.yaml\",\"tag\":\"2025_12\",\"months\":[[\"2025\",\"THÁNG 12\"],[\"2026\",\"THÁNG 01\"]],\"batch_dir\":\"loan-materials-2025-12\",\"source_root\":\"/Volumes/TOSHIBA EXT/HUATEX进出口材料\"}" > $EV/loan_run.log 2>&1
LJOB=$(grep -o 'RESULT job=[^ ]*' $EV/loan_run.log | cut -d= -f2)
LSTATUS=$(grep -o 'RESULT job=[^ ]* status=[^ ]*' $EV/loan_run.log | awk '{print $3}')
echo "Loan job=$LJOB status=$LSTATUS"
LONE=$(find $PKG/HUATEX-Tools/runs/$LJOB/out -name 'Outcome1-*.xlsx' | head -1)
LOUT=$(dirname "$LONE")
echo "Loan out=$LOUT"
python3 "$CMP" --base "$(ls $LBASE/Outcome1-*.xlsx | head -1)" --new "$LONE" > $EV/loan_outcome1_diff.txt 2>&1
echo "Outcome1 退出码=$?" >> $EV/loan_outcome1_diff.txt
cat $EV/loan_outcome1_diff.txt
python3 - <<PY > $EV/loan_outcome2_compare.txt 2>&1
import os, hashlib
def snap(root):
    files, empties = {}, []
    for dp, dns, fns in os.walk(root):
        rel = os.path.relpath(dp, root)
        if not fns and not dns:
            empties.append('' if rel == '.' else rel.replace(os.sep, '/'))
        for f in fns:
            p = os.path.join(dp, f)
            r = os.path.relpath(p, root).replace(os.sep, '/')
            files[r] = hashlib.md5(open(p, 'rb').read()).hexdigest()
    return files, sorted(empties)
b, be = snap('$LBASE/Outcome2')
n, ne = snap('$LOUT/Outcome2')
only_b = sorted(set(b) - set(n)); only_n = sorted(set(n) - set(b))
diff = sorted(k for k in set(b) & set(n) if b[k] != n[k])
print('baseline 文件数 = %d' % len(b)); print('new      文件数 = %d' % len(n))
print('仅基线有 = %d %s' % (len(only_b), only_b[:5]))
print('仅新件有 = %d %s' % (len(only_n), only_n[:5]))
print('md5 不同 = %d %s' % (len(diff), diff[:5]))
print('md5 相同 = %d' % (len(b) - len(diff) - len(only_b)))
print('结论 = %s' % ('PASS: %d/%d md5 全等' % (len(b) - len(diff) - len(only_b), len(b))
                   if not only_b and not only_n and not diff else 'FAIL'))
PY
cat $EV/loan_outcome2_compare.txt
python3 pkg_drive.py download $LJOB Outcome2.zip $DL/Outcome2.zip > $EV/loan_download.txt 2>&1
cat $EV/loan_download.txt
echo "$PSTATUS" > $EV/payment_status.txt
echo "$LSTATUS" > $EV/loan_status.txt

# ─────────── 收尾 ───────────
kill $SRV 2>/dev/null; sleep 1; pkill -f "app/server.py" 2>/dev/null
lsof -ti :8000 >/dev/null 2>&1 && lsof -ti :8000 | xargs kill -9 2>/dev/null
echo "server stopped: $(lsof -ti :8000 | wc -l | tr -d ' ') listeners left" | tee $EV/server_stop.txt
cp $PKG/server.log $EV/pkg_test_server.log 2>/dev/null
echo "=== v1.3.4 回归结束 $(date '+%F %T') ==="
