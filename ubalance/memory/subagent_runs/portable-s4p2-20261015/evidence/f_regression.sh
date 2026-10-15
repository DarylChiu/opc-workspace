#!/bin/bash
# F · 包自包含性回归（S4.2 v1.2）—— 脱离 dev 树，纯 HTTP 驱动，与只读基线逐单元格对拍
set -u
WS=/Users/zhaoyuzhao/.openclaw/workspace-balance
EV=$WS/memory/subagent_runs/portable-s4p2-20261015/evidence
PKG=/tmp/huatex-v12-test
DL=$PKG/dl
ZIP=$WS/deliverables/HUATEX-Tools-Windows-v1.2-20261015.zip
PBASE=$WS/work/payprep-20261013/out
PIN=$WS/work/payprep-20261013/in
LBASE=$WS/work/loan-materials-2025-12/out/v2.8d-2025_12-20261014_1526
LIN=$WS/work/loan-materials-2025-12/in/L1-成品采购入库补单测试20条.xlsx
CMP=$WS/portable/tools/compare_xlsx.py

exec > >(tee $EV/f_regression.log) 2>&1
echo "=== F 回归开始 $(date '+%F %T') ==="

lsof -ti :8000 >/dev/null 2>&1 && { echo "[x] 8000 被占用，先停旧服务"; lsof -ti :8000 | xargs kill -9; sleep 1; }
rm -rf $PKG; mkdir -p $PKG $DL
unzip -q $ZIP -d $PKG || { echo "[x] 解压失败"; exit 1; }
cp $WS/portable/config.regression-2025_12.yaml $PKG/config.regression-2025_12.yaml
echo "[OK] 解压到 $PKG（脱离 dev 树）"
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

# ─────────── Payment（10-13 批次） ───────────
echo "=== Payment 运行 ==="
python3 pkg_drive.py run payment "$PIN/10-12华特明细待确认.xlsx" \
    "$PIN/voucher-a1013.zip" "$PIN/voucher-b1013.zip" "$PIN/voucher-c1013.zip" \
    --params '{"date":"20261013"}' > $EV/payment_run.log 2>&1
PJOB=$(grep -o 'RESULT job=[^ ]*' $EV/payment_run.log | cut -d= -f2)
echo "Payment job=$PJOB"
POUT=$PKG/HUATEX-Tools/runs/$PJOB/out
ls -la "$POUT" 2>/dev/null

: > $EV/payment_diff.txt
for f in "Payment request to Bank-20261013.xlsx" "Payment recon ledger-20261013.xlsx" "Payment 待人工核清单-20261013.xlsx"; do
  echo "################ $f" >> $EV/payment_diff.txt
  python3 "$CMP" --base "$PBASE/$f" --new "$POUT/$f" >> $EV/payment_diff.txt 2>&1
  echo "退出码=$?" >> $EV/payment_diff.txt
done
grep -c "差异总数 = 0" $EV/payment_diff.txt > $EV/payment_diff_pass.txt
echo "md5(recon.txt) base=$(md5 -q "$PBASE/Payment request to Bank-20261013.xlsx.recon.txt") new=$(md5 -q "$POUT/Payment request to Bank-20261013.xlsx.recon.txt")" > $EV/payment_recon_txt_md5.txt
cat $EV/payment_recon_txt_md5.txt
python3 - <<PY > $EV/payment_totals.txt 2>&1
import openpyxl
def tot(p):
    ws = openpyxl.load_workbook(p, data_only=True)['Sheet1']
    s = 0.0; n = 0
    for r in range(2, ws.max_row + 1):
        v = ws.cell(r, 8).value
        if isinstance(v, (int, float)):
            s += v; n += 1
    return ws.max_row, ws.max_column, int(s), n
for tag, p in (('base', '$PBASE/Payment request to Bank-20261013.xlsx'),
               ('new',  '$POUT/Payment request to Bank-20261013.xlsx')):
    r, c, s, n = tot(p)
    print('%s dims %d x %d | H合计= %d | 发票行= %d' % (tag, r, c, s, n))
PY
cat $EV/payment_totals.txt
grep -c "OCR 引擎不可用" $EV/payment_run.log > $EV/payment_ocr_warn_count.txt
echo "OCR 降级警告条数=$(cat $EV/payment_ocr_warn_count.txt)"
cp $PKG/HUATEX-Tools/runs/$PJOB/job.json $EV/payment_job.json 2>/dev/null

# ─────────── Loan（2025_12 等价 override） ───────────
echo "=== Loan 运行（约 5 分钟）==="
python3 pkg_drive.py run loan "$LIN" --params "{\"override\":\"$PKG/config.regression-2025_12.yaml\",\"tag\":\"2025_12\",\"months\":[[\"2025\",\"THÁNG 12\"],[\"2026\",\"THÁNG 01\"]],\"batch_dir\":\"loan-materials-2025-12\",\"source_root\":\"/Volumes/TOSHIBA EXT/HUATEX进出口材料\"}" > $EV/loan_run.log 2>&1
LJOB=$(grep -o 'RESULT job=[^ ]*' $EV/loan_run.log | cut -d= -f2)
echo "Loan job=$LJOB"
LOUT=$(dirname "$(find $PKG/HUATEX-Tools/runs/$LJOB/out -name 'Outcome1-*.xlsx' | head -1)")
echo "Loan out=$LOUT"
ONE=$(find $LOUT -name 'Outcome1-*.xlsx' | head -1)
python3 "$CMP" --base "$(ls $LBASE/Outcome1-*.xlsx | head -1)" --new "$ONE" > $EV/loan_outcome1_diff.txt 2>&1
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
print('基线空目录 = %s' % be); print('新件空目录 = %s' % ne)
print('结论 = %s' % ('PASS: %d/%d md5 全等' % (len(b) - len(diff) - len(only_b), len(b))
                   if not only_b and not only_n and not diff else 'FAIL'))
PY
cat $EV/loan_outcome2_compare.txt
python3 pkg_drive.py download $LJOB Outcome2.zip $DL/Outcome2.zip > $EV/loan_download.txt 2>&1
cat $EV/loan_download.txt
cp $PKG/HUATEX-Tools/runs/$LJOB/job.json $EV/loan_job.json 2>/dev/null
cp $PKG/HUATEX-Tools/runs/$LJOB/logs/run_config.yaml $EV/loan_run_config.yaml 2>/dev/null

# ─────────── 收尾 ───────────
kill $SRV 2>/dev/null; sleep 1; pkill -f "app/server.py" 2>/dev/null
lsof -ti :8000 >/dev/null 2>&1 && lsof -ti :8000 | xargs kill -9 2>/dev/null
echo "server stopped: $(lsof -ti :8000 | wc -l | tr -d ' ') listeners left" > $EV/server_stop.txt
cp $PKG/server.log $EV/pkg_test_server.log 2>/dev/null
echo "=== F 回归结束 $(date '+%F %T') ==="
