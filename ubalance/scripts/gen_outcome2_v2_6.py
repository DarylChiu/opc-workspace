#!/usr/bin/env python3
"""
gen_outcome2_v2_6.py — v2.6 Outcome2 三件套材料包(2023 HUATEX)
铁律1: 严格从 L1 出发；铁律2: 内容级判定，只拷保留文件
三件套 = Invoice PDF + 已通关ToKhai QDTQ(金额勾稽选中) + B/L/SWB/AWB
输出到硬盘: HUATEX贷款材料/Outcome2-v2.6-{月份}-{时间}/{STT}-{发票号}/
用法: python3 gen_outcome2_v2_6.py "THÁNG 1-2023"
"""
import os, sys, re, shutil
sys.path.insert(0, os.path.dirname(__file__))
from tokhai_extract import extract_tokhai, is_tokhai_filename
from doc_classify import classify_file
import openpyxl
from datetime import datetime

try:
    import pdfplumber
    PDF_READY = True
except ImportError:
    PDF_READY = False

DISK = '/Volumes/TOSHIBA EXT/HUATEX贷款材料'
L1 = os.path.join(DISK, 'L1-Raw Materials-Year2023.xlsx')
RM2023 = os.path.join(DISK, 'RM-Database/2023')
TS = datetime.now().strftime('%Y%m%d_%H%M')
TOL = 0.001

# 参数支持: 单月 "THÁNG 1-2023" | 范围 "1-6" | 单月数字 "3" | 空=全量
ARG = sys.argv[1] if len(sys.argv) > 1 else None
def resolve_months(arg):
    if not arg:
        return None, 'ALL'
    m = re.match(r'^(\d{1,2})\s*-\s*(\d{1,2})$', arg.strip())
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return {f'THÁNG {i}-2023' for i in range(a, b + 1)}, f'{a}to{b}'
    if re.match(r'^\d{1,2}$', arg.strip()):
        return {f'THÁNG {int(arg)}-2023'}, f'M{int(arg)}'
    return {arg}, re.sub(r'[^0-9A-Za-z]', '', arg)
MONTH_SET, tag = resolve_months(ARG)
OUTDIR = os.path.join(DISK, f'Outcome2-v2.6-{tag}-{TS}')

# 文件分类改用共享 doc_classify.classify_file

# 读 L1（唯一起点）
wb = openpyxl.load_workbook(L1, data_only=True)
ws = wb.active
l1_rows = []
for row in ws.iter_rows(min_row=4, values_only=True):
    if not row or len(row) < 6 or not row[2]:
        continue
    inv = str(row[2]).strip()
    if inv == 'None':
        continue
    try: amt = float(row[5]) if row[5] is not None else None
    except (ValueError, TypeError): amt = None
    l1_rows.append({'stt': row[0], 'inv': inv, 'amount': amt})
wb.close()

# RM-Database 目录索引
months = sorted(MONTH_SET) if MONTH_SET else sorted(os.listdir(RM2023))
dir_paths = []
for m in months:
    mp = os.path.join(RM2023, m)
    if not os.path.isdir(mp): continue
    for d in sorted(os.listdir(mp)):
        dp = os.path.join(mp, d)
        if os.path.isdir(dp):
            dir_paths.append((d, dp))

def find_dir(inv):
    for d, dp in dir_paths:
        core = re.sub(r'^\s*\d+\.\s*', '', d).strip()
        if inv in re.split(r'\s+', core):
            return dp
    return None

os.makedirs(OUTDIR, exist_ok=True)
report = []
complete = incomplete = missing_dir = 0

for rec in l1_rows:
    inv = rec['inv']
    dp = find_dir(inv)
    if MONTH_SET and not dp:
        continue  # 月份样张：只处理本月能找到目录的
    stt = rec['stt']
    outsub = os.path.join(OUTDIR, f'{stt}-{inv}')
    if not dp:
        missing_dir += 1
        report.append(f'{stt}-{inv}: ⚠️ RM-Database无目录')
        continue
    os.makedirs(outsub, exist_ok=True)
    files = [f for f in os.listdir(dp) if os.path.isfile(os.path.join(dp, f))]
    # 分类 + 收集通关ToKhai
    keep = []          # (类别, 文件名)
    cleared = []       # (extract结果, 文件名)
    for f in files:
        fp = os.path.join(dp, f)
        cat, r = classify_file(fp)
        if cat == 'TOKHAI_QDTQ':
            cleared.append((r, f))
        elif cat in ('INVOICE_PDF','BL','SWB','AWB'):
            keep.append((cat, f))
    # ToKhai 方案B：金额勾稽选中属于本发票的通关单
    picked_tokhai = [(r, f) for r, f in cleared
                     if r['amount'] is not None and rec['amount'] is not None
                     and abs(r['amount']-rec['amount']) < TOL]
    for r, f in picked_tokhai:
        keep.append(('TOKHAI_QDTQ', f))
    # 拷贝保留文件
    copied = set()
    for cat, f in keep:
        if f in copied:
            continue
        src = os.path.join(dp, f)
        dst = os.path.join(outsub, f)
        try:
            shutil.copy2(src, dst)
            copied.add(f)
        except Exception as e:
            report.append(f'{stt}-{inv}: 拷贝失败 {f}: {e}')
    # 完整性
    cats = set(c for c, _ in keep)
    has_inv = 'INVOICE_PDF' in cats or 'TOKHAI_QDTQ' in cats
    has_bl = bool(cats & {'BL','SWB','AWB'})
    has_tk = 'TOKHAI_QDTQ' in cats
    if has_inv and has_bl:
        complete += 1
        status = '✅完整'
    else:
        incomplete += 1
        miss = []
        if not has_inv: miss.append('Invoice')
        if not has_bl: miss.append('B/L')
        if not has_tk: miss.append('ToKhai')
        status = '⚠️缺'+','.join(miss)
    report.append(f'{stt}-{inv}: {status} | 拷贝{len(copied)}件 '
                  f'[Inv:{sum(1 for c,_ in keep if c=="INVOICE_PDF")} '
                  f'ToKhai:{sum(1 for c,_ in keep if c=="TOKHAI_QDTQ")} '
                  f'BL/AWB:{sum(1 for c,_ in keep if c in("BL","SWB","AWB"))}]')

# 写处理报告
rp = os.path.join(OUTDIR, f'处理报告-Outcome2-v2.6-{tag}-{TS}.txt')
with open(rp, 'w') as f:
    f.write(f'Outcome2 v2.6 三件套材料包 | {datetime.now():%Y-%m-%d %H:%M}\n')
    f.write(f'范围: {ARG or "全部"} | 严格L1驱动 + 内容级判定\n')
    f.write('='*70+'\n')
    f.write(f'完整: {complete} | 不完整: {incomplete} | 无目录: {missing_dir}\n')
    f.write('='*70+'\n')
    for line in report:
        f.write(line+'\n')

print(f'✅ Outcome2 已输出到硬盘: {OUTDIR}')
print(f'完整三件套: {complete} | 不完整: {incomplete} | 无目录: {missing_dir}')
print(f'处理报告: {rp}')
for line in report:
    print('  '+line)
