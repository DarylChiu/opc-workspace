#!/bin/bash
# v1.3-20261016 · 冒烟回归（Payment 核销 10-13 批次）——脱离 dev 树，纯 HTTP 驱动，与只读基线逐单元格对拍
set -u
WS=/Users/zhaoyuzhao/.openclaw/workspace-balance
EV=$WS/memory/subagent_runs/huatex-v1.3-20261016/evidence
PKG=/tmp/huatex-v13-test
DL=$PKG/dl
ZIP=$WS/deliverables/HUATEX-Tools-Windows-v1.3-20261016.zip
PBASE=$WS/work/payprep-20261013/out
PIN=$WS/work/payprep-20261013/in
CMP=$WS/portable/tools/compare_xlsx.py

exec > >(tee $EV/f_regression.log) 2>&1
echo "=== F 回归（v1.3）开始 $(date '+%F %T') ==="

lsof -ti :8000 >/dev/null 2>&1 && { echo "[!] 8000 被占用，先停旧服务"; lsof -ti :8000 | xargs kill -9; sleep 1; }
rm -rf $PKG; mkdir -p $PKG $DL
unzip -q "$ZIP" -d $PKG || { echo "[x] 解压失败"; exit 1; }
echo "[OK] 解压到 $PKG（脱离 dev 树）"
cd "$PKG/HUATEX-Tools" || exit 1
echo "[i] 包根 ls:"; ls
python3 tools/preflight.py --selftest > $EV/pkg_test_preflight.log 2>&1
echo "preflight rc=$?" >> $EV/pkg_test_preflight.log
echo "[OK] 包内自检 → $EV/pkg_test_preflight.log"

nohup python3 app/server.py > $PKG/server.log 2>&1 &
SRV=$!; echo $SRV > $PKG/server.pid
sleep 4

cp $WS/memory/subagent_runs/portable-s4p2-20261015/evidence/pkg_drive.py $DL/
cd $DL
python3 pkg_drive.py state > $EV/api_state.json 2>&1 && echo "[OK] 服务已起 pid=$SRV" || { echo "[x] 服务未起"; cat $PKG/server.log; exit 1; }
python3 pkg_drive.py save-root "/Volumes/TOSHIBA EXT/HUATEX进出口材料" > $EV/page0_save_source_root.txt 2>&1
cat $EV/page0_save_source_root.txt

# ─────────── Payment（10-13 批次，4 个文件） ───────────
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
echo "差异总数=0 的行数 = $(cat $EV/payment_diff_pass.txt)（应为 3）"
echo "base=$(md5 -q "$PBASE/Payment request to Bank-20261013.xlsx.recon.txt") new=$(md5 -q "$POUT/Payment request to Bank-20261013.xlsx.recon.txt")" > $EV/payment_recon_txt_md5.txt
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

# ─────────── 收尾 ───────────
kill $SRV 2>/dev/null; sleep 1; pkill -f "app/server.py" 2>/dev/null
lsof -ti :8000 >/dev/null 2>&1 && lsof -ti :8000 | xargs kill -9 2>/dev/null
sleep 1
echo "server stopped: $(lsof -ti :8000 | wc -l | tr -d ' ') listeners left" > $EV/server_stop.txt
cat $EV/server_stop.txt
cp $PKG/server.log $EV/pkg_test_server.log 2>/dev/null
echo "=== F 回归（v1.3）结束 $(date '+%F %T') ==="
