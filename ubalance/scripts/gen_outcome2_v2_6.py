#!/usr/bin/env python3
"""
gen_outcome2_v2_6.py — Outcome2 贷款材料包生成器（内部版本 v2.8.0）

铁律1: 严格从 L1 出发；铁律2: 内容级判定，不看文件名
五类材料全保留(Daryl 7/15): Invoice(货物/设备,物流发票除外) + Sales Contract/Confirmation
                          + Packing List + B/L或Sea Waybill(空运AWB) + 已通关ToKhai(金额勾稽)
精准匹配(Daryl 7/15): 材料必须匹配 L1 发票号；引用他票的剔除；
                      未读到票号的运输单据视为该批次船务共享单据保留；ToKhai 按金额勾稽。

★ v2.8.0 变更（2026-10-03 Daryl 定，修正两个复发性问题）:
  【修正1 · 不再生成分类子目录】
    合订本(清关资料 PDF = SC+Invoice+PL 在同一文件)以前会被按多标签“按类各拷一份”，
    造成 1_SalesConfirmation / 2_Invoice / 3_PackingList 三份同一 PDF 的重复。
    → 现在**输出扁平**：每票号一个文件夹，一个文件只出现一次；
      「覆盖了哪几类」改由同目录的 `材料清单.txt` 记录，不再靠物理复制表达。
  【修正2 · 重复文件去重】
    a) 内容去重：md5 完全一致 → 只留一份（含跨批次子目录的同一份文件）
    b) 同文档多版本去重：归一化文件名（去 --已盖章 / (1) / 尾部空格 / __N 后缀）
       → 优先保留带「盖章」者，否则保留体积最大者；被丢弃者在 `材料清单.txt` 列明，不静默丢件。
  【修正3 · 支持批次子目录】
    2026 起 RM-Database 票号目录下按「胚布/纱线/机织/成品」等子目录分装 → 改为递归扫描。
  【新增 · 可复用参数】
    --l1 <path>  --rm <dir>  --l1-start-row N  --out <dir>   便于跨批次复用（不再写死 2023）。

用法:
  python3 gen_outcome2_v2_6.py "THÁNG 1-2023" | "4-6" | "3" | 空=全量
  python3 gen_outcome2_v2_6.py --l1 /path/L1.xlsx --rm /path/RM-Database/2026 --out /path/Outcome2
"""
import os, sys, re, shutil, hashlib
sys.path.insert(0, os.path.dirname(__file__))
from doc_classify import classify_keep_ex, attribute_file, amount_in_text, _cache_save
import openpyxl
from datetime import datetime

VERSION = 'v2.8.0'
DISK = '/Volumes/TOSHIBA EXT/HUATEX贷款材料'
L1 = os.path.join(DISK, 'L1-Raw Materials-Year2023.xlsx')
RM = os.path.join(DISK, 'RM-Database/2023')
MONTH_PREFIX = 'THÁNG'
MONTH_SUFFIX = '-2023'
L1_START_ROW = 4
OUTDIR_OVERRIDE = None
TS = datetime.now().strftime('%Y%m%d_%H%M')
TOL = 0.001

# ---------- 参数解析 ----------
argv = sys.argv[1:]
ARG = None
i = 0
while i < len(argv):
    a = argv[i]
    if a == '--l1' and i + 1 < len(argv):
        L1 = argv[i+1]; i += 2
    elif a == '--rm' and i + 1 < len(argv):
        RM = argv[i+1]; i += 2
    elif a == '--l1-start-row' and i + 1 < len(argv):
        L1_START_ROW = int(argv[i+1]); i += 2
    elif a == '--out' and i + 1 < len(argv):
        OUTDIR_OVERRIDE = argv[i+1]; i += 2
    elif a == '--month-prefix' and i + 1 < len(argv):
        MONTH_PREFIX = argv[i+1]; i += 2
    elif a == '--month-suffix' and i + 1 < len(argv):
        MONTH_SUFFIX = argv[i+1]; i += 2
    else:
        ARG = a; i += 1

def resolve_months(arg):
    if not arg:
        return None, 'ALL'
    m = re.match(r'^(\d{1,2})\s*-\s*(\d{1,2})$', arg.strip())
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return {f'{MONTH_PREFIX} {i:02d}{MONTH_SUFFIX}' for i in range(a, b + 1)}, f'{a}to{b}'
    if re.match(r'^\d{1,2}$', arg.strip()):
        return {f'{MONTH_PREFIX} {int(arg):02d}{MONTH_SUFFIX}'}, f'M{int(arg)}'
    return {arg}, re.sub(r'[^0-9A-Za-z]', '', arg)

MONTH_SET, tag = resolve_months(ARG)
OUTDIR = OUTDIR_OVERRIDE or os.path.join(DISK, f'Outcome2-{VERSION}-{tag}-{TS}')

# ---------- 读 L1（唯一起点） ----------
wb = openpyxl.load_workbook(L1, data_only=True)
ws = wb.active
l1_rows = []
for row in ws.iter_rows(min_row=L1_START_ROW, values_only=True):
    if not row or len(row) < 6 or not row[2]:
        continue
    inv = str(row[2]).strip()
    if inv == 'None':
        continue
    try:
        amt = float(row[5]) if row[5] is not None else None
    except (ValueError, TypeError):
        amt = None
    l1_rows.append({'stt': row[0], 'inv': inv, 'amount': amt})
wb.close()
L1_INVS = {r['inv'] for r in l1_rows}
L1_PREFIXES = {re.match(r'^[A-Za-z]+', i).group(0).upper() for i in L1_INVS if re.match(r'^[A-Za-z]+', i)}

# ---------- RM-Database 目录索引 ----------
def list_months():
    if MONTH_SET:
        # 兼容 "THÁNG 09"/"THÁNG 9"/目录实际命名
        found = []
        for d in sorted(os.listdir(RM)):
            if not os.path.isdir(os.path.join(RM, d)):
                continue
            norm = re.sub(r'\s+', ' ', d).strip().upper()
            for m in MONTH_SET:
                mn = re.sub(r'\s+', ' ', m).strip().upper()
                alt = mn.replace('THÁNG 0', 'THÁNG ')
                if norm in (mn, alt):
                    found.append(d)
        return sorted(set(found))
    return sorted(os.listdir(RM))

dir_paths = []
for m in list_months():
    mp = os.path.join(RM, m)
    if not os.path.isdir(mp):
        continue
    for d in sorted(os.listdir(mp)):
        dp = os.path.join(mp, d)
        if os.path.isdir(dp) and not d.startswith('._'):
            dir_paths.append((d, dp))

def _dir_tokens(d):
    core = re.sub(r'^\s*\d+\.\s*', '', d).strip()
    out = set()
    for t in re.split(r'[\s+,，]+', core):
        t = t.strip().strip('-').strip()
        if re.match(r'^[A-Za-z]{2,10}\d{3,}(-\d+)?$', t):
            out.add(t)
    return out

def find_dir(inv):
    for d, dp in dir_paths:
        if inv in _dir_tokens(d):
            return dp
    m = re.match(r'^(.*?)-\d+$', inv)
    if m:
        base = m.group(1)
        for d, dp in dir_paths:
            if base in _dir_tokens(d):
                return dp
    return None

# ---------- 工具 ----------
def md5f(p):
    h = hashlib.md5()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()

def norm_name(nm):
    """同文档多版本归一：去 --已盖章/盖章/副本/(1)/__N/尾部空白，再剔非字母数字汉字"""
    s = os.path.splitext(nm)[0]
    s = re.sub(r'[-_\s]*(已盖章|盖章|副本|摘录|\(\d+\)|__\d+)\s*$', '', s)
    s = re.sub(r'[^0-9A-Za-z\u4e00-\u9fff]+', '', s)
    return s.upper()

def walk_files(dp):
    """递归收集（v2.8: 支持 胚布/纱线/机织/成品 等批次子目录）"""
    out = []
    for r, dns, fns in os.walk(dp):
        dns[:] = [x for x in dns if not x.startswith('._') and x != '__MACOSX']
        for f in sorted(fns):
            if f.startswith('._') or f.startswith('~$') or f == '.DS_Store':
                continue
            out.append((f, os.path.join(r, f)))
    return out

TRANSPORT = {'BL', 'SWB', 'AWB'}
BUSINESS = {'INVOICE', 'SALES_CONTRACT', 'PACKING_LIST'}

os.makedirs(OUTDIR, exist_ok=True)
report = []
complete = incomplete = missing_dir = 0

for rec in l1_rows:
    inv = rec['inv']
    dp = find_dir(inv)
    if MONTH_SET and not dp:
        continue
    stt = rec['stt']
    outsub = os.path.join(OUTDIR, f'{stt}-{inv}')
    if not dp:
        missing_dir += 1
        report.append(f'{stt}-{inv}: ⚠️ RM-Database无目录')
        continue
    os.makedirs(outsub, exist_ok=True)

    files = walk_files(dp)
    _core = re.sub(r'^\s*\d+\.\s*', '', os.path.basename(dp)).strip()
    dir_invs = {t for t in re.split(r'[\s+,，]+', _core)
                if re.match(r'^[A-Za-z]{2,10}\d{4,}(-\d+)?$', t) and t != inv
                and (re.match(r'^[A-Za-z]+', t).group(0).upper() in L1_PREFIXES)}
    biz_cands = L1_INVS | dir_invs

    keep = []            # (tags, filename, srcpath)
    cleared = []         # (extract结果, filename, srcpath)
    dropped_other = []
    unattributed = []
    amt_hits = 0
    for f, fp in files:
        try:
            ok, tags, r, text = classify_keep_ex(fp)
        except Exception as e:
            report.append(f'{stt}-{inv}: 分类失败 {f}: {e}')
            continue
        if not ok:
            continue
        if 'TOKHAI_QDTQ' in tags:
            cleared.append((r, f, fp))
            continue
        cands = biz_cands if (tags & BUSINESS) else L1_INVS
        att = attribute_file(text, f, inv, cands)
        if att.startswith('other:'):
            dropped_other.append(f'{f}→{att[6:]}')
            continue
        if att == 'neutral' and (tags & BUSINESS):
            unattributed.append(f)
        if att == 'match' and amount_in_text(text, f, rec['amount']):
            amt_hits += 1
        keep.append((tags, f, fp))

    picked_tokhai = [(r, f, fp) for r, f, fp in cleared
                     if r['amount'] is not None and rec['amount'] is not None
                     and abs(r['amount'] - rec['amount']) < TOL]
    for r, f, fp in picked_tokhai:
        keep.append(({'TOKHAI_QDTQ'}, f, fp))

    # ===== v2.8 去重 + 扁平拷贝（不再建 1/2/3 分类子目录）=====
    seen_md5, used_names, copied_names, dropped_dup = {}, set(), [], []
    cand = []
    for tags, f, fp in keep:
        try:
            h = md5f(fp)
        except Exception:
            continue
        if h in seen_md5:
            dropped_dup.append((f, '内容完全重复(md5一致)'))
            continue
        seen_md5[h] = fp
        cand.append((tags, f, fp))
    groups = {}
    for tags, f, fp in cand:
        groups.setdefault(norm_name(f), []).append((tags, f, fp))
    picked = []
    for k, items in groups.items():
        if len(items) == 1:
            picked.append(items[0]); continue
        items.sort(key=lambda x: (0 if '盖章' in x[1] else 1, -os.path.getsize(x[2])))
        picked.append(items[0])
        for x in items[1:]:
            dropped_dup.append((x[1], f'同文档其他版本(保留 {items[0][1]})'))
    picked.sort(key=lambda x: x[1])
    for tags, f, fp in picked:
        nm = f
        if nm in used_names:
            b, e = os.path.splitext(f); n = 2
            while f'{b}__{n}{e}' in used_names:
                n += 1
            nm = f'{b}__{n}{e}'
        used_names.add(nm)
        try:
            shutil.copy2(fp, os.path.join(outsub, nm))
            copied_names.append((nm, sorted(tags)))
        except Exception as e:
            report.append(f'{stt}-{inv}: 拷贝失败 {f}: {e}')

    # 材料清单.txt（代替物理分类子目录）
    with open(os.path.join(outsub, '材料清单.txt'), 'w', encoding='utf-8') as fh:
        fh.write(f'票号：{inv}\n生成：{datetime.now():%Y-%m-%d %H:%M}　生成器：{VERSION}\n')
        fh.write(f'文件数：{len(copied_names)}（每个文件只存一份；合订本可同时覆盖多类）\n')
        fh.write('五类：Sales Confirmation / Invoice / Packing List / B/L或Sea Waybill(AWB) / 已通关ToKhai\n')
        fh.write('-' * 64 + '\n')
        for nm, tags in copied_names:
            fh.write(f'\n{nm}\n    覆盖类别：{" / ".join(tags)}\n')
        if dropped_dup:
            fh.write('\n' + '-' * 64 + '\n已去重未收（不静默丢件，此处留痕）：\n')
            for nm, why in dropped_dup:
                fh.write(f'    - {nm}  ← {why}\n')
        if dropped_other:
            fh.write('\n他票干扰已剔除：\n')
            for x in dropped_other:
                fh.write(f'    - {x}\n')

    allt = set()
    for tags, f, fp in keep:
        allt |= tags
    has_inv = 'INVOICE' in allt
    has_sc = 'SALES_CONTRACT' in allt
    has_pl = 'PACKING_LIST' in allt
    has_bl = bool(allt & TRANSPORT)
    has_tk = 'TOKHAI_QDTQ' in allt
    combo = [f for tags, f, fp in keep if 'INVOICE' in tags and (tags & TRANSPORT)]
    if (has_inv or has_sc or has_pl) and has_bl and has_tk:
        complete += 1
        status = '✅完整'
    else:
        incomplete += 1
        miss = []
        if not (has_inv or has_sc or has_pl): miss.append('业务单据')
        if not has_bl: miss.append('B/L')
        if not has_tk: miss.append('ToKhai')
        status = '⚠️缺' + ','.join(miss)
    extras = ''
    if combo:
        extras += ' | 📌Invoice在B/L文件内: ' + '; '.join(combo)
    if dropped_other:
        extras += f' | 🚫剔除他票干扰({len(dropped_other)}): ' + '; '.join(dropped_other)
    if unattributed:
        extras += f' | ⚠️未读到票号待复核: ' + '; '.join(unattributed)
    if dropped_dup:
        extras += f' | 🧹去重{len(dropped_dup)}件'
    inv_n = sum(1 for t, _, _ in keep if 'INVOICE' in t)
    sc_n = sum(1 for t, _, _ in keep if 'SALES_CONTRACT' in t)
    pl_n = sum(1 for t, _, _ in keep if 'PACKING_LIST' in t)
    bl_n = sum(1 for t, _, _ in keep if t & TRANSPORT)
    tk_n = sum(1 for t, _, _ in keep if 'TOKHAI_QDTQ' in t)
    n_att = sum(1 for t, _, _ in keep if 'TOKHAI_QDTQ' not in t)
    report.append(f'{stt}-{inv}: {status} | 落盘{len(copied_names)}件 '
                  f'[Inv:{inv_n} SC:{sc_n} PL:{pl_n} BL:{bl_n} TK:{tk_n}] '
                  f'票号匹配:{n_att - len(unattributed)}/{n_att} 金额命中:{amt_hits}{extras}')

rp = os.path.join(OUTDIR, f'处理报告-Outcome2-{VERSION}-{tag}-{TS}.txt')
with open(rp, 'w', encoding='utf-8') as f:
    f.write(f'Outcome2 {VERSION} 贷款材料包（五类全保留 + 票号金额勾稽 + 扁平输出 + 去重） | {datetime.now():%Y-%m-%d %H:%M}\n')
    f.write(f'范围: {ARG or "全部"} | L1: {L1} | RM: {RM}\n')
    f.write('规则: 业务单据=Inv/SC/PL(须匹配L1票号,他票剔除) | 运输=BL/SWB/AWB(无票号视为共享船务单据) | ToKhai=已通关+金额勾稽\n')
    f.write('v2.8: ①扁平输出,不建1/2/3分类子目录(合订本只存一份) ②md5+同名多版本双重去重 ③递归扫描批次子目录\n')
    f.write('=' * 70 + '\n')
    f.write(f'完整: {complete} | 不完整: {incomplete} | 无目录: {missing_dir}\n')
    f.write('=' * 70 + '\n')
    for line in report:
        f.write(line + '\n')

_cache_save()
print(f'✅ Outcome2 已输出: {OUTDIR}')
print(f'完整: {complete} | 不完整: {incomplete} | 无目录: {missing_dir}')
print(f'处理报告: {rp}')
for line in report:
    print('  ' + line)
