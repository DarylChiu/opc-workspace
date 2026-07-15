#!/usr/bin/env python3
"""
gen_outcome2_v2_6.py — v2.7.0 Outcome2 贷款材料包(2023 HUATEX)
铁律1: 严格从 L1 出发；铁律2: 内容级判定，只拷保留文件
五类材料全保留(Daryl 7/15): Invoice(货物/设备,物流发票除外) + Sales Contract/Confirmation
                          + Packing List + B/L或Sea Waybill(空运AWB) + 已通关ToKhai(金额勾稽)
精准匹配(Daryl 7/15): 材料必须匹配 L1 发票号——引用其他票号的文件(兄弟票/共享目录他票)剔除；
                      未读到票号的运输单据视为该批次船务共享单据保留；ToKhai按金额勾稽。
输出到硬盘: HUATEX贷款材料/Outcome2-v2.6-{月份}-{时间}/{STT}-{发票号}/
用法: python3 gen_outcome2_v2_6.py "THÁNG 1-2023" | "4-6" | "3" | 空=全量
"""
import os, sys, re, shutil
sys.path.insert(0, os.path.dirname(__file__))
from doc_classify import classify_keep_ex, attribute_file, amount_in_text, _cache_save
import openpyxl
from datetime import datetime

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
L1_INVS = {r['inv'] for r in l1_rows}
L1_PREFIXES = {re.match(r'^[A-Za-z]+', i).group(0).upper() for i in L1_INVS if re.match(r'^[A-Za-z]+', i)}   # 全年322票，用于他票干扰判定

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

def _dir_tokens(d):
    """目录名 → 发票号token集。处理: 序号前缀/+连接/尾部破折号/数量标注/品牌前缀"""
    core = re.sub(r'^\s*\d+\.\s*', '', d).strip()
    out = set()
    for t in re.split(r'[\s+]+', core):
        t = t.strip().strip('-').strip()
        if re.match(r'^[A-Za-z]{2,}\d{3,}(-\d+)?$', t):
            out.add(t)
    return out

def find_dir(inv):
    # 一遍精确 token
    for d, dp in dir_paths:
        if inv in _dir_tokens(d):
            return dp
    # 二遍: 兄弟票 X-N 回退到 base X 的目录(RM-Database常不为-1单独建目录)
    m = re.match(r'^(.*?)-\d+$', inv)
    if m:
        base = m.group(1)
        for d, dp in dir_paths:
            if base in _dir_tokens(d):
                return dp
    return None

TRANSPORT = {'BL', 'SWB', 'AWB'}
BUSINESS = {'INVOICE', 'SALES_CONTRACT', 'PACKING_LIST'}

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
    # 目录名中的发票号token(共享目录他票，可能不在L1): 如 "11.HMABFZ230136 + HMA23009"
    _core = re.sub(r'^\s*\d+\.\s*', '', os.path.basename(dp)).strip()
    dir_invs = {t for t in re.split(r'[\s+]+', _core)
                if re.match(r'^[A-Za-z]{2,10}\d{4,}(-\d+)?$', t) and t != inv
                and (re.match(r'^[A-Za-z]+', t).group(0).upper() in L1_PREFIXES)}
    biz_cands = L1_INVS | dir_invs   # 业务单据的他票判定候选
    # 多标签分类 + 发票号归属 + ToKhai金额勾稽
    keep = []            # (标签集, 文件名, 归属)
    cleared = []         # (extract结果, 文件名)
    dropped_other = []   # 引用他票号被剔除的干扰文件
    unattributed = []    # 未读到票号的业务单据(保留+待复核)
    amt_hits = 0         # 内容中读到L1金额的保留文件数
    for f in files:
        fp = os.path.join(dp, f)
        ok, tags, r, text = classify_keep_ex(fp)
        if not ok:
            continue
        if 'TOKHAI_QDTQ' in tags:
            cleared.append((r, f))
            continue
        # 业务单据(Inv/SC/PL)用 L1∪目录token 判他票; 运输单据只用L1(避免误伤引用B/L号的提单)
        cands = biz_cands if (tags & BUSINESS) else L1_INVS
        att = attribute_file(text, f, inv, cands)
        if att.startswith('other:'):
            dropped_other.append(f'{f}→{att[6:]}')
            continue
        if att == 'neutral' and (tags & BUSINESS):
            unattributed.append(f)
        if att == 'match' and amount_in_text(text, f, rec['amount']):
            amt_hits += 1
        keep.append((tags, f))
    # ToKhai 方案B：金额勾稽选中属于本发票的通关单（排除兄弟票通关单）
    picked_tokhai = [(r, f) for r, f in cleared
                     if r['amount'] is not None and rec['amount'] is not None
                     and abs(r['amount']-rec['amount']) < TOL]
    for r, f in picked_tokhai:
        keep.append(({'TOKHAI_QDTQ'}, f))
    # 拷贝所有保留文件
    copied = set()
    for tags, f in keep:
        if f in copied:
            continue
        src = os.path.join(dp, f)
        dst = os.path.join(outsub, f)
        try:
            shutil.copy2(src, dst)
            copied.add(f)
        except Exception as e:
            report.append(f'{stt}-{inv}: 拷贝失败 {f}: {e}')
    # 覆盖统计（5类）
    allt = set()
    for tags, _ in keep:
        allt |= tags
    has_inv = 'INVOICE' in allt
    has_sc = 'SALES_CONTRACT' in allt
    has_pl = 'PACKING_LIST' in allt
    has_bl = bool(allt & TRANSPORT)
    has_tk = 'TOKHAI_QDTQ' in allt
    # 合订标记：某文件同时含 Invoice 与 提单
    combo = [f for tags, f in keep if 'INVOICE' in tags and (tags & TRANSPORT)]
    # 完整 = 有业务单据(Inv/SC/PL) + 有运输单据 + 有已通关ToKhai
    # 完整 = 业务单据 + 运输单据 + 已通关ToKhai（五类口径，缺一即标）
    if (has_inv or has_sc or has_pl) and has_bl and has_tk:
        complete += 1
        status = '✅完整'
    else:
        incomplete += 1
        miss = []
        if not (has_inv or has_sc or has_pl): miss.append('业务单据')
        if not has_bl: miss.append('B/L')
        if not has_tk: miss.append('ToKhai')
        status = '⚠️缺'+','.join(miss)
    # 标记
    extras = ''
    if combo:
        extras += ' | 📌Invoice在B/L文件内: ' + '; '.join(combo)
    if dropped_other:
        extras += f' | 🚫剔除他票干扰({len(dropped_other)}): ' + '; '.join(dropped_other)
    if unattributed:
        extras += f' | ⚠️未读到票号待复核: ' + '; '.join(unattributed)
    inv_n = sum(1 for t,_ in keep if 'INVOICE' in t)
    sc_n = sum(1 for t,_ in keep if 'SALES_CONTRACT' in t)
    pl_n = sum(1 for t,_ in keep if 'PACKING_LIST' in t)
    bl_n = sum(1 for t,_ in keep if t & TRANSPORT)
    tk_n = sum(1 for t,_ in keep if 'TOKHAI_QDTQ' in t)
    n_att = sum(1 for t,_ in keep if 'TOKHAI_QDTQ' not in t)
    report.append(f'{stt}-{inv}: {status} | 拷贝{len(copied)}件 '
                  f'[Inv:{inv_n} SC:{sc_n} PL:{pl_n} BL:{bl_n} TK:{tk_n}] '
                  f'票号匹配:{n_att - len(unattributed)}/{n_att} 金额命中:{amt_hits}{extras}')

# 写处理报告
rp = os.path.join(OUTDIR, f'处理报告-Outcome2-v2.6-{tag}-{TS}.txt')
with open(rp, 'w') as f:
    f.write(f'Outcome2 v2.7.0 贷款材料包(5类全保留+票号金额勾稽) | {datetime.now():%Y-%m-%d %H:%M}\n')
    f.write(f'范围: {ARG or "全部"} | 严格L1驱动 + 内容级判定 + 发票号归属\n')
    f.write('规则: 业务单据=Inv/SC/PL(须匹配L1票号,他票剔除) | 运输=BL/SWB/AWB(无票号视为共享船务单据) | ToKhai=已通关+金额勾稽\n')
    f.write('='*70+'\n')
    f.write(f'完整: {complete} | 不完整: {incomplete} | 无目录: {missing_dir}\n')
    f.write('='*70+'\n')
    for line in report:
        f.write(line+'\n')

_cache_save()
print(f'✅ Outcome2 已输出到硬盘: {OUTDIR}')
print(f'完整(业务单据+运输单据): {complete} | 不完整: {incomplete} | 无目录: {missing_dir}')
print(f'处理报告: {rp}')
for line in report:
    print('  '+line)
