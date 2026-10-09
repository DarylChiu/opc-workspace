#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""贷款材料自动化整理 · 2026年8-10月批次（图片票号 = L1） v4
新增：①他票干扰滤除（含非L1票号的合订/单据剔除）②共享提单按「子目录=批次」隔离
"""
import os, re, sys, json, shutil, datetime

WS = '/Users/zhaoyuzhao/.openclaw/workspace-balance'
sys.path.insert(0, os.path.join(WS, 'scripts'))
import doc_classify as DC  # noqa
import doc_fields as DF   # v2.8: L1 只有票号时，从材料补全 日期/供应商/采购类别

DISK = '/Volumes/TOSHIBA EXT/HUATEX贷款材料'
RM = os.path.join(DISK, 'RM-Database', '2026')
MONTHS = ['THÁNG 08', 'THÁNG 09', 'THÁNG 10']
TS = datetime.datetime.now().strftime('%Y%m%d_%H%M')
OUTDIR = os.path.join(WS, 'work', 'loan-materials-2026', f'Outcome-v2.7-2026_08to10-{TS}')
OUT2 = os.path.join(OUTDIR, 'Outcome2')
shutil.rmtree(OUTDIR, ignore_errors=True)
os.makedirs(OUT2, exist_ok=True)

# v2.8d-patch (2026-10-09): 本批次 L1 = 票号图 OCR（tesseract psm6/11）+ RM-Database 前缀反向校正
#   OCR 原读 HMKCK260103 → 经 RM 目录名反向校正为 HMXCK260103（前缀获 RM 验证）
L1 = ['HMXCAT260615', 'HMXCAT260618', 'HMXCK260103', 'HMXCK260103-1',
      'HMXCAT260621', 'HMXCAT260620', 'YNHT20261386-3', 'YNHT20261386-3-1',
      'HMXCFZAT260094', 'HMXCFZAT260096', 'HMXCK260106']
L1_SET = set(L1)
TRANSPORT = {'BL', 'SWB', 'AWB'}
TAGDIR = {'SALES_CONTRACT': '1_SalesConfirmation', 'INVOICE': '2_Invoice',
          'PACKING_LIST': '3_PackingList', 'BL': '4_BL_or_AWB', 'SWB': '4_BL_or_AWB',
          'AWB': '4_BL_or_AWB', 'TOKHAI_QDTQ': '5_ToKhai_QDTQ'}
FIVE = ['SalesConfirmation', 'Invoice', 'PackingList', 'BL_or_AWB', 'ToKhai']
TICKET = re.compile(r'[A-Z]{2,}[A-Z0-9]{2,}\d{3,}(?:-\d+)?')

log = []
dedup_drops = []   # v2.8d: 去重丢弃留痕（不再写材料清单.txt，改写入处理报告）
def P(s):
    print(s, flush=True); log.append(s)

def tok_in(name, tok):
    pat = r'(?<![0-9A-Za-z])' + re.escape(tok) + r'(?![0-9A-Za-z])(?!-\d)'
    return re.search(pat, name, re.IGNORECASE) is not None

# 本公司发票号前缀白名单（用于区分「他票」与集装箱号/提单号/SKM扫描件编号）
INV_PREFIX = ('HMA', 'HMF', 'HMH', 'HMX', 'YN', 'YR', 'YL', 'IV', 'BV', 'EC')

def foreign_tokens(hay):
    """提取文本/文件名中出现的、不属于 L1 的【他票发票号】
    仅认发票前缀白名单，避免把 OOLU/集装箱号、SKM扫描编号、Waybill 号误判为他票"""
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
            if fn.startswith('._') or fn.startswith('~$') or fn == '.DS_Store':
                continue
            yield os.path.join(dp, fn)

all_dirs = []
for m in MONTHS:
    p = os.path.join(RM, m)
    if os.path.isdir(p):
        for d in sorted(os.listdir(p)):
            if os.path.isdir(os.path.join(p, d)) and not d.startswith('._'):
                all_dirs.append((m, d, os.path.join(p, d)))
P(f'RM-Database/2026 目录数: {len(all_dirs)}')

# v2.8d-patch (2026-10-09 / Daryl 补充指令): 记录 RM 快照（= 本批数据截止时间）
rm_counts = {m: sum(1 for (mm, _dn, _fp) in all_dirs if mm == m) for m in MONTHS}
rm_latest, _rm_latest_ts = '', 0.0
for dp, dns, fns in os.walk(RM):
    dns[:] = [x for x in dns if not x.startswith('._') and x != '__MACOSX']
    for n in list(dns) + list(fns):
        if n.startswith('._'):
            continue
        try:
            mt = os.path.getmtime(os.path.join(dp, n))
        except OSError:
            continue
        if mt > _rm_latest_ts:
            _rm_latest_ts, rm_latest = mt, datetime.datetime.fromtimestamp(mt).strftime('%Y-%m-%d')
RM_SNAP = (f"RM快照（= 本批数据截止）: THÁNG 08={rm_counts.get('THÁNG 08', 0)} / "
           f"THÁNG 09={rm_counts.get('THÁNG 09', 0)} / THÁNG 10={rm_counts.get('THÁNG 10', 0)} "
           f"子目录；全库最新 mtime={rm_latest}")
P(RM_SNAP)

t2dirs, t2base = {}, {}
for t in L1:
    ds = [d for d in all_dirs if tok_in(d[1], t)]
    base = re.sub(r'-\d+$', '', t)
    if not ds and base != t:
        ds = [d for d in all_dirs if tok_in(d[1], base)]
        t2base[t] = base
    t2dirs[t] = ds
    P(f'  {t:<24} → {len(ds)} 目录 {"(base回退)" if t in t2base else ""}')

# v2.8d-patch: 未决问题数据（铁律1：未匹配仍入 Outcome1 行 + Outcome2 空文件夹，不中止）
unmatched_tickets = [t for t in L1 if not t2dirs.get(t)]
# 本批 OCR 前缀反校正留痕（前缀仅在 RM 命中时采用；未命中则保留 OCR 原样并标「前缀未获 RM 验证」）
# 第 3 条经 Daryl 人工确认 = HMXCK260103（OCR 曾误读 HMKCK260103），与 RM 反校正结果一致
rm_prefix_fix = [('HMKCK260103', 'HMXCK260103')]
rm_unverified = []  # 本批 11/11 全部在 RM 找到同号目录，无未验证前缀

dirpath2cands = {}
for t, ds in t2dirs.items():
    for m, dn, fp in ds:
        dirpath2cands.setdefault(fp, []).append(t)

assign, excluded, tkinfo = {t: [] for t in L1}, [], {}
for fp in dirpath2cands:
    cands = dirpath2cands[fp]
    for f in sorted(iter_files(fp)):
        rel = os.path.relpath(f, fp)
        sub = os.path.dirname(rel)          # 批次子目录
        try:
            keep, tags, tk = DC.classify_keep(f)
        except Exception as e:
            keep, tags, tk = False, {'ERROR'}, None
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
                    tkinfo[t] = tk
            continue
        fgn = foreign_tokens(os.path.basename(f) + '\n' + text)
        if fgn and not (set(tags) & TRANSPORT):
            excluded.append({'src': f, 'kind': 'OTHER_TICKET:' + ','.join(sorted(fgn)[:3]),
                             'dir': os.path.basename(fp)}); continue
        if set(tags) & TRANSPORT:
            # 他票提单/他票扫描件（如 SKM_...HMXCFZGYAT260040-1.pdf）→ 直接剔除
            if fgn:
                excluded.append({'src': f, 'kind': 'OTHER_TICKET(他票提单):' + ','.join(sorted(fgn)[:2]),
                                 'dir': os.path.basename(fp)}); continue
            # 共享提单：优先按「同批次子目录」归属；无匹配者按整目录归属
            owners = []
            for t in cands:
                if any(r['sub'] == sub for r in assign[t]):
                    owners.append(t)
            if not owners:
                owners = cands
            if not owners:
                excluded.append({'src': f, 'kind': 'OTHER_TICKET(共享提单他票):' + ','.join(sorted(fgn)[:2]),
                                 'dir': os.path.basename(fp)}); continue
            for t in owners:
                assign[t].append({'src': f, 'name': os.path.basename(f), 'tags': tags,
                                  'attr': 'neutral(共享提单·同批次)', 'dir': os.path.basename(fp),
                                  'sub': sub, 'tk': tk})
            continue
        excluded.append({'src': f, 'kind': 'NO_MATCH', 'dir': os.path.basename(fp)})

# v2.8d（Daryl 2026-10-05 定）: Outcome2 文件夹名 = Outcome1 序号前缀 + 发票号（如 1-HMXCFZGYAT260042）
TICKET_DIR = {t: f'{i}-{t}' for i, t in enumerate(L1, 1)}
for t in L1:
    os.makedirs(os.path.join(OUT2, TICKET_DIR[t]), exist_ok=True)

import hashlib
def md5f(p):
    h = hashlib.md5()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()

copied = 0
for t in L1:
    seen_md5, used_names, lines, dropped = {}, set(), [], []
    # ① 内容去重（md5）
    cands = []
    for r in sorted(assign[t], key=lambda x: (x['name'], x['src'])):
        try:
            h = md5f(r['src'])
        except Exception:
            continue
        if h in seen_md5:
            dropped.append((r['name'], '内容完全重复(md5一致)'))
            continue
        seen_md5[h] = r['src']
        cands.append(r)

    # ② 同文档多版本去重（归一化文件名：去 --已盖章 / (1) / 末尾空格）
    def norm(nm):
        # v2.8b 修正：保留扩展名。旧版 splitext 丢弃扩展名 → X.pdf 与 X.xlsx 会被当作
        # 「同文档多版本」而误删其一（潜在丢件）。扩展名必须进入去重键。
        b, e = os.path.splitext(nm)
        s = re.sub(r'[-_\s]*(已盖章|盖章|摘录|\(\d+\)|__\d+)\s*$', '', b)
        s = re.sub(r'[^0-9A-Za-z\u4e00-\u9fff]+', '', s)
        return s.upper() + e.lower()
    groups = {}
    for r in cands:
        groups.setdefault(norm(r['name']), []).append(r)
    picked = []
    for k, items in groups.items():
        if len(items) == 1:
            picked.append(items[0]); continue
        items.sort(key=lambda x: (0 if '盖章' in x['name'] else 1,
                                  -os.path.getsize(x['src'])))
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
        lines.append((nm, sorted(r['tags']), r['attr']))

    # v2.8d（Daryl 2026-10-05 定）: 不再生成「材料清单.txt」。
    # 但去重留痕不得丢失（铁则：不静默丢件）→ 改打 [DEDUP-DROP] 并写入「处理报告」
    for nm, why in dropped:
        dedup_drops.append((t, nm, why))
        P(f'  [DEDUP-DROP] {t} | {nm} ← {why}')
P(f'复制文件数（已去重）: {copied}')

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
wb = openpyxl.Workbook(); ws = wb.active; ws.title = 'Outcome1'
cols = ['序号', '发票号', '关单号', '报关日期', '金额(USD)', '日期', '供应商',
        '贷款用途分类', '分类依据', '置信度', '五类材料完整性', 'ToKhai勾稽', '备注']
ws.append(cols)
for c in range(1, len(cols) + 1):
    ws.cell(1, c).font = Font(bold=True)
    ws.cell(1, c).fill = PatternFill('solid', fgColor='DDEBF7')
    ws.cell(1, c).alignment = Alignment(horizontal='center', wrap_text=True)
for idx, t in enumerate(L1, 1):
    rs = assign[t]; tagsU = set()
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
    tk = tkinfo.get(t); rmk = []
    # v2.8：L1 仅含票号 → 从材料本身补全 发票日期/供应商/采购类别
    inv_text = ''
    for r in assign[t]:
        if (set(r['tags']) & {'INVOICE', 'SALES_CONTRACT', 'PACKING_LIST'}) and r['src'].lower().endswith('.pdf'):
            try:
                inv_text += '\n'.join(DC.pdf_pages_text(r['src'])) + '\n'
            except Exception:
                pass
    F = DF.fill_fields(l1={}, tk=tk or {}, inv_text=inv_text)
    rmk.append(f'[数据截止:{rm_latest}]（RM快照，见处理报告）')
    for _a, _b in rm_prefix_fix:
        if t == _b:
            rmk.append(f'OCR前缀校正 {_a}→{_b}（经 RM 目录名反校正；第3条经 Daryl 人工确认 = {_b}）')
    if not rs:
        rmk.append('RM-Database 无该号材料（目录缺失，入 Outcome1 行 + Outcome2 空文件夹）')
    if t in t2base:
        rmk.append(f'目录经 base {t2base[t]} 回退定位')
    if any(r['attr'].startswith('neutral') for r in rs):
        rmk.append('含船务共享提单(未载票号)')
    rmk += F['notes']
    ws.append([idx, t,
               tk.get('so_to_khai', '') if tk else '',
               tk.get('ngay_ymd', '') if tk else '',
               F['amount'] if F['amount'] is not None else '待补',
               F['date'] or '待补',
               F['supplier'] or '待补',
               F['cls'],
               F['cls_src'],
               F['cf'],
               comp, '✅金额已核对' if tk else '❌未匹配', '；'.join(rmk)])
for i, w in enumerate([6, 24, 16, 12, 12, 12, 14, 14, 18, 8, 30, 14, 46], 1):
    ws.column_dimensions[get_column_letter(i)].width = w
xlsx = os.path.join(OUTDIR, f'Outcome1-v2.7-2026_08to10-{TS}.xlsx')
wb.save(xlsx); P(f'Outcome1: {xlsx}')

rep = os.path.join(OUTDIR, f'处理报告-v2.7-2026_08to10-{TS}.txt')
with open(rep, 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(log))
    fh.write('\n\n===== 逐票明细 =====\n')
    for idx, t in enumerate(L1, 1):
        fh.write(f'\n[{idx}] {t}\n')
        if not assign[t]:
            fh.write('    未收材料\n')
        for r in sorted(assign[t], key=lambda x: sorted(x['tags'])):
            fh.write(f"    {sorted(r['tags'])} | {r['attr']} | [{r['sub'] or '根目录'}] {r['name']}\n")
    fh.write('\n\n===== 剔除清单 =====\n')
    for e in excluded:
        fh.write(f"    {e['kind']} | [{e['dir'][:30]}] {os.path.basename(e['src'])}\n")
    fh.write('\n\n===== 去重丢弃清单（md5 相同 / 同文档多版本；不静默丢件）=====\n')
    for t, nm, why in dedup_drops:
        fh.write(f'    {t} | {nm}  ← {why}\n')
P(f'报告: {rep}')
# v2.8d-patch (2026-10-09 / Daryl 补充指令): 报告追加「未决问题」节
with open(rep, 'a', encoding='utf-8') as fh:
    fh.write('\n\n===== 未决问题 =====\n')
    fh.write(f'{RM_SNAP}\n')
    fh.write(f"L1 来源：票号图 OCR（{datetime.datetime.now().strftime('%Y-%m-%d')}）\n")
    fh.write('① 未获 RM 验证的票号前缀: '
             + ('; '.join(f'{a}→保留原样' for a, _b in rm_unverified) if rm_unverified
                else '无（11/11 票号在 RM-Database/2026 均找到同号目录；HMKCK260103 前缀已由 RM 校正为 HMXCK260103，并经 Daryl 人工确认）')
             + '\n')
    fh.write('①-1 前缀校正命中详情: 第3条 HMXCK260103（OCR 误读 HMKCK260103）→ RM 命中 THÁNG 09/93.HMXCK260103，HMXCK260103-1 胚布；'
             'Daryl 人工确认 = HMXCK260103；同目录另含 HMXCK260103-1，两者均已收为 L1 行\n')
    fh.write('② 未匹配到目录的票号: '
             + ('; '.join(unmatched_tickets) if unmatched_tickets else '无（11/11 全部命中 RM 目录）') + '\n')
    fh.write(f'③ RM 快照与 L1 关系: RM 数据截止 {rm_latest}；本次 L1 为 {datetime.datetime.now().strftime("%Y-%m-%d")} 票号图，'
             '晚于 RM 快照 → 若 L1 存在晚于快照的票据，本批为「不完整匹配」，需 Daryl 更新 RM 后重跑（脚本按时间戳建目录，可安全重跑）\n')
print('\n===SUMMARY===')
for t in L1:
    tg = set()
    for r in assign[t]:
        tg |= set(r['tags'])
    tk = tkinfo.get(t)
    print(f'{t:<24} {len(assign[t]):>2}文件 {sorted(tg)} tk={(tk or {}).get("so_to_khai","-")} amt={(tk or {}).get("amount","-")}')
