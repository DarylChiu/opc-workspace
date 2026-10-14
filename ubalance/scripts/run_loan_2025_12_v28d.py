#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""进出口材料自动化处理 · 2025年12月批次（L1 = Excel，20 行） **v2.8d**

来源：run_loan_v29_20261013.py（2026 批次 v2.9 运行器）
差异（本次唯一改动 = 环境修正 + 输入形态）：
  1. DISK 由旧 `HUATEX贷款材料` → 新 `HUATEX进出口材料`（Toshiba 重新挂载后改名）
  2. RM 搜索跨月/跨年：2025/THÁNG 12 + 2026/THÁNG 01
  3. L1 由 Excel 读入（全部 20 行；带「供应商」列；无金额列）
  4. `-N` 兄弟票双向回退（base↔-N 皆尝试）；命中率与备注照 v2.8d
  5. Outcome1 = **13 列**（v2.8d；不含 v2.9 的「放行日」）
  6. 输出写回 Toshiba 新路径 + work 暂存

**铁律（v2.8d 不变）**：
  · 一切从 L1 出发：L1 有、RM 无 → 标「无目录」入 Outcome1 行 + Outcome2 空文件夹，绝不新增行
  · 打开文件读内容，不看文件名
"""
import os, re, sys, json, shutil, datetime

WS = '/Users/zhaoyuzhao/.openclaw/workspace-balance'
sys.path.insert(0, os.path.join(WS, 'scripts'))
import doc_classify as DC  # noqa
import doc_fields as DF    # noqa

DISK = '/Volumes/TOSHIBA EXT/HUATEX进出口材料'
RM = os.path.join(DISK, 'RM-Database')
MONTHS = [('2025', 'THÁNG 12'), ('2026', 'THÁNG 01')]
BATCH = '2025_12'
TS = datetime.datetime.now().strftime('%Y%m%d_%H%M')
STAGE = os.path.join(WS, 'work', 'loan-materials-2025-12', 'out', f'v2.8d-{BATCH}-{TS}')
OUT2 = os.path.join(STAGE, 'Outcome2')
shutil.rmtree(STAGE, ignore_errors=True)
os.makedirs(OUT2, exist_ok=True)

L1_XLSX = os.path.join(WS, 'work/loan-materials-2025-12/in/L1-成品采购入库补单测试20条.xlsx')

TRANSPORT = {'BL', 'SWB', 'AWB'}
FIVE = ['SalesConfirmation', 'Invoice', 'PackingList', 'BL_or_AWB', 'ToKhai']
TICKET = re.compile(r'[A-Z]{2,}[A-Z0-9]{2,}\d{3,}(?:-\d+)?')
INV_PREFIX = ('HMA', 'HMF', 'HMH', 'HMX', 'NHF', 'YN', 'YR', 'YL', 'IV', 'BV', 'EC', 'OP')

log = []
dedup_drops = []


def P(s):
    print(s, flush=True)
    log.append(s)


# ---------- 读 L1（唯一起点） ----------
import openpyxl
wb = openpyxl.load_workbook(L1_XLSX, data_only=True)
ws = wb['Sheet1']
L1, L1_SUP = [], {}
for row in ws.iter_rows(values_only=True):
    if not row or not row[0]:
        continue
    inv = str(row[0]).strip()
    if not re.match(r'^[A-Z]{2,}[A-Z0-9]*\d{3,}(?:-\d+){0,2}$', inv):
        continue  # 跳表头/空行
    L1.append(inv)
    if len(row) > 1 and row[1]:
        L1_SUP[inv] = str(row[1]).strip()
wb.close()
L1_SET = set(L1)
P(f'L1 行数: {len(L1)}（来源 {os.path.basename(L1_XLSX)}）')
P('L1: ' + ', '.join(L1))
assert L1, 'L1 为空，中止'


def tok_in(name, tok):
    pat = r'(?<![0-9A-Za-z])' + re.escape(tok) + r'(?![0-9A-Za-z])(?!-\d)'
    return re.search(pat, name, re.IGNORECASE) is not None


def tok_in_loose(name, tok):
    """允许 -N 后缀（用于 base→兄弟目录 回退）"""
    pat = r'(?<![0-9A-Za-z])' + re.escape(tok) + r'-\d+(?![0-9A-Za-z])'
    return re.search(pat, name, re.IGNORECASE) is not None


def foreign_tokens(hay):
    out = set()
    for m in TICKET.finditer((hay or '').upper()):
        tk = m.group(0)
        if tk in L1_SET:
            continue
        if not tk.startswith(INV_PREFIX):
            continue
        if any(tok_in(hay, t) for t in L1_SET):
            continue
        out.add(tk)
    return out


def iter_files(root):
    for dp, dns, fns in os.walk(root):
        dns[:] = [x for x in dns if not x.startswith('._') and x != '__MACOSX']
        for fn in fns:
            if fn.startswith('._') or fn.startswith('~$') or fn == '.DS_Store' or fn == 'Thumbs.db':
                continue
            yield os.path.join(dp, fn)


# ---------- RM 目录索引（跨月/跨年） ----------
all_dirs = []
for y, m in MONTHS:
    p = os.path.join(RM, y, m)
    if not os.path.isdir(p):
        P(f'[WARN] 缺目录: {p}')
        continue
    for d in sorted(os.listdir(p)):
        dp = os.path.join(p, d)
        if os.path.isdir(dp) and not d.startswith('._'):
            all_dirs.append((f'{y}/{m}', d, dp))
P(f'RM 目录数（{" + ".join(f"{y}/{m}" for y, m in MONTHS)}）: {len(all_dirs)}')

# RM 快照
rm_latest, _ts = '', 0.0
for y, m in MONTHS:
    p = os.path.join(RM, y, m)
    for dp, dns, fns in os.walk(p):
        dns[:] = [x for x in dns if not x.startswith('._') and x != '__MACOSX']
        for n in list(dns) + list(fns):
            if n.startswith('._'):
                continue
            try:
                mt = os.path.getmtime(os.path.join(dp, n))
            except OSError:
                continue
            if mt > _ts:
                _ts, rm_latest = mt, datetime.datetime.fromtimestamp(mt).strftime('%Y-%m-%d')
RM_SNAP = f'RM快照（= 本批数据截止）: 全库最新 mtime={rm_latest}'
P(RM_SNAP)

# ---------- 匹配（exact → base 回退 → -N 兄弟回退） ----------
t2dirs, t2base, t2sib = {}, {}, {}
for t in L1:
    ds = [d for d in all_dirs if tok_in(d[1], t)]
    if ds:
        t2dirs[t] = ds
        P(f'  {t:<24} → {len(ds)} 目录 [exact]')
        continue
    base = re.sub(r'-\d+$', '', t)
    if base != t:
        ds = [d for d in all_dirs if tok_in(d[1], base)]
        if ds:
            t2dirs[t] = ds
            t2base[t] = base
            P(f'  {t:<24} → {len(ds)} 目录 [base {base} 回退]')
            continue
    else:
        ds = [d for d in all_dirs if tok_in_loose(d[1], base)]
        if ds:
            t2dirs[t] = ds
            t2sib[t] = ds[0][1]
            P(f'  {t:<24} → {len(ds)} 目录 [-N 兄弟回退]')
            continue
    t2dirs[t] = []
    P(f'  {t:<24} → 0 目录 [无目录]')

unmatched_tickets = [t for t in L1 if not t2dirs.get(t)]

# ---------- 归属 ----------
dirpath2cands = {}
for t, ds in t2dirs.items():
    for m, dn, fp in ds:
        dirpath2cands.setdefault(fp, []).append(t)

assign, excluded, tkinfo = {t: [] for t in L1}, [], {}
tk_cands = {}

for fp in dirpath2cands:
    cands = dirpath2cands[fp]
    for f in sorted(iter_files(fp)):
        rel = os.path.relpath(f, fp)
        sub = os.path.dirname(rel)
        try:
            keep, tags, tk = DC.classify_keep(f)
        except Exception as e:
            excluded.append({'src': f, 'kind': f'ERROR:{e!s:.40}', 'dir': os.path.basename(fp)})
            continue
        if not keep:
            excluded.append({'src': f, 'kind': next(iter(tags), 'OTHER'), 'dir': os.path.basename(fp)})
            continue
        text = ''
        if f.lower().endswith('.pdf'):
            try:
                text = '\n'.join(DC.pdf_pages_text(f))
            except Exception:
                pass
        elif tk and tk.get('so_hoa_don'):
            text = f"{tk.get('so_hoa_don')} {tk.get('so_to_khai','')}"
        attrs = {t: DC.attribute_file(text, os.path.basename(f), t, L1_SET) for t in cands}
        matched = [t for t in cands if attrs[t] == 'match']
        if matched:
            for t in matched:
                assign[t].append({'src': f, 'name': os.path.basename(f), 'tags': tags,
                                  'attr': 'match', 'dir': os.path.basename(fp), 'sub': sub, 'tk': tk})
                if tk and tk.get('so_to_khai'):
                    tk_cands.setdefault(t, []).append(tk)
            continue
        fgn = foreign_tokens(os.path.basename(f) + '\n' + text)
        if fgn and not (set(tags) & TRANSPORT):
            excluded.append({'src': f, 'kind': 'OTHER_TICKET:' + ','.join(sorted(fgn)[:3]),
                             'dir': os.path.basename(fp)})
            continue
        if set(tags) & TRANSPORT:
            if fgn:
                excluded.append({'src': f, 'kind': 'OTHER_TICKET(他票提单):' + ','.join(sorted(fgn)[:2]),
                                 'dir': os.path.basename(fp)})
                continue
            owners = [t for t in cands if any(r['sub'] == sub for r in assign[t])]
            if not owners:
                owners = cands
            for t in owners:
                assign[t].append({'src': f, 'name': os.path.basename(f), 'tags': tags,
                                  'attr': 'neutral(共享提单·同批次)', 'dir': os.path.basename(fp),
                                  'sub': sub, 'tk': tk})
            continue
        excluded.append({'src': f, 'kind': 'NO_MATCH', 'dir': os.path.basename(fp)})

# ToKhai 选优选（多张取 关单号/金额 最完整者；prefer QDTQ）
for t, lst in tk_cands.items():
    lst.sort(key=lambda r: (0 if 'QDTQ' in (r.get('file') or '').upper() else 1,
                            -(len(str(r.get('so_to_khai') or ''))),
                            0 if r.get('amount') is not None else 1))
    tkinfo[t] = lst[0]

# ---------- Outcome2：扁平 + 序号前缀文件夹 ----------
TICKET_DIR = {t: f'{i}-{t}' for i, t in enumerate(L1, 1)}
for t in L1:
    os.makedirs(os.path.join(OUT2, TICKET_DIR[t]), exist_ok=True)


def md5f(p):
    import hashlib
    h = hashlib.md5()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


copied = 0
for t in L1:
    seen_md5, used_names, dropped = {}, set(), []
    cands2 = []
    for r in sorted(assign[t], key=lambda x: (x['name'], x['src'])):
        try:
            h = md5f(r['src'])
        except Exception:
            continue
        if h in seen_md5:
            dropped.append((r['name'], '内容完全重复(md5一致)'))
            continue
        seen_md5[h] = r['src']
        cands2.append(r)

    def norm(nm):
        b, e = os.path.splitext(nm)
        s = re.sub(r'[-_\s]*(已盖章|盖章|摘录|\(\d+\)|__\d+)\s*$', '', b)
        s = re.sub(r'[^0-9A-Za-z\u4e00-\u9fff]+', '', s)
        return s.upper() + e.lower()

    groups = {}
    for r in cands2:
        groups.setdefault(norm(r['name']), []).append(r)
    picked = []
    for k, items in groups.items():
        if len(items) == 1:
            picked.append(items[0])
            continue
        items.sort(key=lambda x: (0 if '盖章' in x['name'] else 1, -os.path.getsize(x['src'])))
        picked.append(items[0])
        for x in items[1:]:
            dropped.append((x['name'], '同文档其他版本（保留 ' + items[0]['name'] + '）'))

    picked.sort(key=lambda x: x['name'])
    for r in picked:
        nm = r['name']
        b, e = os.path.splitext(nm)
        if nm in used_names:
            i = 2
            while f'{b}__{i}{e}' in used_names:
                i += 1
            nm = f'{b}__{i}{e}'
        used_names.add(nm)
        try:
            shutil.copy2(r['src'], os.path.join(OUT2, TICKET_DIR[t], nm))
            copied += 1
        except Exception as ex:
            P(f'  [COPY-ERR] {nm}: {ex}')
    for nm, why in dropped:
        dedup_drops.append((t, nm, why))
        P(f'  [DEDUP-DROP] {t} | {nm} ← {why}')
P(f'复制文件数（已去重）: {copied}')

# ---------- Outcome1（13 列 v2.8d） ----------
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
wb = openpyxl.Workbook()
ws = wb.active
ws.title = 'Outcome1'
cols = ['序号', '发票号', '关单号', '报关日期', '金额(USD)', '日期', '供应商',
        '贷款用途分类', '分类依据', '置信度', '五类材料完整性', 'ToKhai勾稽', '备注']
ws.append(cols)
for c in range(1, len(cols) + 1):
    ws.cell(1, c).font = Font(bold=True)
    ws.cell(1, c).fill = PatternFill('solid', fgColor='DDEBF7')
    ws.cell(1, c).alignment = Alignment(horizontal='center', wrap_text=True)

for idx, t in enumerate(L1, 1):
    rs = assign[t]
    tagsU = set()
    for r in rs:
        tagsU |= set(r['tags'])
    have = set()
    if 'SALES_CONTRACT' in tagsU: have.add('SalesConfirmation')
    if 'INVOICE' in tagsU: have.add('Invoice')
    if 'PACKING_LIST' in tagsU: have.add('PackingList')
    if tagsU & TRANSPORT: have.add('BL_or_AWB')
    if 'TOKHAI_QDTQ' in tagsU: have.add('ToKhai')
    miss = [x for x in FIVE if x not in have]
    comp = '✅完整' if not miss else '⚠️缺' + '/'.join(miss)
    tk = tkinfo.get(t)
    rmk = []
    inv_text = ''
    for r in assign[t]:
        if (set(r['tags']) & {'INVOICE', 'SALES_CONTRACT', 'PACKING_LIST'}) and r['src'].lower().endswith('.pdf'):
            try:
                inv_text += '\n'.join(DC.pdf_pages_text(r['src'])) + '\n'
            except Exception:
                pass
    F = DF.fill_fields(l1={'supplier': L1_SUP.get(t, '')}, tk=tk or {}, inv_text=inv_text)
    rmk.append(f'[数据截止:{rm_latest}]（RM快照，见处理报告）')
    if not rs:
        rmk.append('RM-Database 无该号材料（目录缺失，入 Outcome1 行 + Outcome2 空文件夹）')
    if t in t2base:
        rmk.append(f'目录经 base {t2base[t]} 回退定位')
    if t in t2sib:
        rmk.append(f'目录经 -N 兄弟目录 {t2sib[t]} 回退定位')
    if any(r['attr'].startswith('neutral') for r in rs):
        rmk.append('含船务共享提单(未载票号)')
    rmk += F['notes']
    ws.append([idx, t,
               (tk or {}).get('so_to_khai', ''),
               (tk or {}).get('ngay_ymd', ''),
               F['amount'] if F['amount'] is not None else '待补',
               F['date'] or '待补',
               F['supplier'] or '待补',
               F['cls'], F['cls_src'], F['cf'],
               comp, '✅金额已核对' if tk else '❌未匹配', '；'.join(rmk)])

for i, w in enumerate([6, 22, 16, 12, 12, 14, 22, 16, 30, 8, 20, 14, 52], 1):
    ws.column_dimensions[get_column_letter(i)].width = w
xlsx = os.path.join(STAGE, f'Outcome1-v2.8d-{BATCH}-{TS}.xlsx')
wb.save(xlsx)
P(f'Outcome1: {xlsx}')

# ---------- 处理报告 ----------
rep = os.path.join(STAGE, f'处理报告-v2.8d-{BATCH}-{TS}.txt')
with open(rep, 'w', encoding='utf-8') as fh:
    fh.write(f'进出口材料自动化处理 v2.8d · 批次 {BATCH} · {datetime.datetime.now():%Y-%m-%d %H:%M}\n')
    fh.write(f'L1: {L1_XLSX}（{len(L1)} 行）\nRM: {RM}（{" + ".join(f"{y}/{m}" for y, m in MONTHS)}）\n')
    fh.write('=' * 70 + '\n')
    fh.write('\n'.join(log))
    fh.write('\n\n===== 逐票明细 =====\n')
    for idx, t in enumerate(L1, 1):
        fh.write(f'\n[{idx}] {t}\n')
        if not assign[t]:
            fh.write('    未收材料（无目录）\n')
        for r in sorted(assign[t], key=lambda x: (sorted(x['tags']), x['name'])):
            fh.write(f"    {sorted(r['tags'])} | {r['attr']} | [{r['sub'] or '根目录'}] {r['name']}\n")
    fh.write('\n\n===== 剔除清单 =====\n')
    for e in excluded:
        fh.write(f"    {e['kind']} | [{e['dir'][:34]}] {os.path.basename(e['src'])}\n")
    fh.write('\n\n===== 去重丢弃清单（md5 相同 / 同文档多版本；不静默丢件）=====\n')
    if not dedup_drops:
        fh.write('    （无）\n')
    for t, nm, why in dedup_drops:
        fh.write(f'    {t} | {nm}  ← {why}\n')
    fh.write('\n\n===== 未决问题 =====\n')
    fh.write(RM_SNAP + '\n')
    fh.write(f'L1 来源：Excel「{os.path.basename(L1_XLSX)}」（Sheet1，{len(L1)} 行）\n')
    fh.write('① 未匹配到目录的票号: '
             + (', '.join(unmatched_tickets) if unmatched_tickets else '无') + '\n')
    fh.write('② 经 base 回退定位的票号: '
             + (', '.join(f'{k}←{v}' for k, v in t2base.items()) if t2base else '无') + '\n')
    fh.write('③ 经 -N 兄弟目录回退定位的票号: '
             + (', '.join(f'{k}←{v}' for k, v in t2sib.items()) if t2sib else '无') + '\n')
P(f'报告: {rep}')

with open(rep, 'a', encoding='utf-8') as fh:
    fh.write('\n\n===== 五类完整性汇总 =====\n')
    for idx, t in enumerate(L1, 1):
        tagsU = set()
        for r in assign[t]:
            tagsU |= set(r['tags'])
        have = set()
        if 'SALES_CONTRACT' in tagsU: have.add('SalesConfirmation')
        if 'INVOICE' in tagsU: have.add('Invoice')
        if 'PACKING_LIST' in tagsU: have.add('PackingList')
        if tagsU & TRANSPORT: have.add('BL_or_AWB')
        if 'TOKHAI_QDTQ' in tagsU: have.add('ToKhai')
        miss = [x for x in FIVE if x not in have]
        fh.write(f"    {idx}-{t}: {'✅完整' if not miss else '⚠️缺'+'/'.join(miss)} "
                 f"({len(assign[t])} 件)\n")

print('\n===SUMMARY===')
for idx, t in enumerate(L1, 1):
    tg = set()
    for r in assign[t]:
        tg |= set(r['tags'])
    tk = tkinfo.get(t)
    print(f'{idx}-{t:<22} {len(assign[t]):>2}件 {sorted(tg)} '
          f'tk={(tk or {}).get("so_to_khai","-")} amt={(tk or {}).get("amount","-")}')
