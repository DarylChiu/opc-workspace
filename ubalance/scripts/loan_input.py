#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""loan_input.py — 「进出口材料自动化处理 v2.8d」输入归一化器

把 Daryl 给的**任意形式输入**统一成「发票号清单」（= L1 等价物）：
  · .xlsx / .xls / .xlsm  → 全表扫描，取票号 token
  · .txt / .csv / .md     → 文本取票号 token
  · 图片 .png/.jpg/.jpeg/.tif/.bmp/.webp → 本机 tesseract OCR（psm 6 + psm 11）后取 token

用法:
  python3 scripts/loan_input.py --in <路径> [<路径> ...] [--out <票号清单.txt>]
                               [--rm "/Volumes/TOSHIBA EXT/HUATEX贷款材料/RM-Database/2026"]
                               [--loose] [--ocr-fix/--no-ocr-fix]

规则（Daryl 2026-10-05 定）:
  1. **不反向索取 L1**：Excel / txt / 截图 都是本项目合法输入，直接开工
  2. **绝不新增/要求 L1 之外的对照**：Outcome 即取数基准（下游交采购部发起请款）
  3. 截图前缀常不可靠（小图 OCR）→ `--ocr-fix` 用 RM-Database **目录名反向校正**（按数字段匹配）
"""
import os
import re
import sys
import glob
import argparse
import subprocess
import difflib

# 发票号白名单前缀（与 run_loan_2026_0810.py 的 INV_PREFIX 对齐）
INV_PREFIX = ('HMA', 'HMF', 'HMH', 'HMX', 'HMHT', 'YN', 'YR', 'YL', 'IV', 'BV', 'EC', 'OP')

# 票号 token：字母前缀(2+) + 数字(3+)，可带 -N 兄弟票后缀
# v2.8d-patch (2026-10-09): 后缀放宽到最多两段 (-N 及 -N-1)，否则 YNHT20261386-3-1
# 会被截断成 YNHT20261386-3 → 静默丢 L1 行（违反铁律1）。
TOKEN_RE = re.compile(r'(?<![0-9A-Za-z])([A-Z]{2,}[A-Z0-9]*\d{3,}(?:-\d+){0,2})(?![0-9A-Za-z])')

# 各种连字符/减号（U+2010/2011/2012/2013/2014/2015/2212/FF0D）统一成 ASCII '-'
_DASHES = dict.fromkeys(map(ord, '\u2010\u2011\u2012\u2013\u2014\u2015\u2212\uff0d\u00ad'), '-')


def norm_dash(s):
    return (s or '').translate(_DASHES)


def tokens_from_text(text, loose=False):
    out = []
    for m in TOKEN_RE.finditer(norm_dash((text or '').upper())):
        tk = m.group(1)
        if not loose and not tk.startswith(INV_PREFIX):
            continue
        out.append(tk)
    return out


def text_from_xlsx(path):
    try:
        import openpyxl
    except ImportError:
        print('  [WARN] openpyxl 不可用，跳过 %s' % path, file=sys.stderr)
        return ''
    chunks = []
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            for v in row:
                if v is None:
                    continue
                chunks.append(str(v))
    wb.close()
    return '\n'.join(chunks)


def text_from_image(path):
    """本机 tesseract（云多模态不可用，2026-10-03 定型）"""
    tesseract = '/opt/homebrew/bin/tesseract' if os.path.exists('/opt/homebrew/bin/tesseract') else 'tesseract'
    out = []
    for psm in ('6', '11'):
        try:
            r = subprocess.run([tesseract, path, 'stdout', '-l', 'eng', '--psm', psm],
                               capture_output=True, text=True, timeout=120)
            out.append(r.stdout or '')
        except Exception as e:
            print('  [WARN] OCR(%s) 失败: %s' % (psm, e), file=sys.stderr)
    return '\n'.join(out)


def text_from_file(path):
    low = path.lower()
    if low.endswith(('.xlsx', '.xlsm', '.xls')):
        return text_from_xlsx(path)
    if low.endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.webp', '.heic')):
        return text_from_image(path)
    with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
        return fh.read()


def rm_dir_names(rm_root):
    names = []
    for p in glob.glob(os.path.join(rm_root, '*', '*')):
        if os.path.isdir(p) and not os.path.basename(p).startswith('._'):
            names.append(os.path.basename(p))
    return names


def match_in_rm(token, names):
    """token 是否出现在 RM 目录名中（连字符先归一化，避开非 ASCII 连字符导致的假失配）"""
    tk = norm_dash(token)
    pat = re.compile(r'(?<![0-9A-Za-z])' + re.escape(tk) + r'(?![0-9A-Za-z])', re.I)
    return [n for n in names if pat.search(norm_dash(n))]


def ocr_fix(token, names):
    """OCR/手误前缀不可靠 → 用 RM-Database 目录名反向校正。

    只在「数字段完全一致 + 兄弟票后缀一致 + 字母前缀高度相似（difflib ≥ 0.6）」时改写，
    并取相似度最高者；否则返回 None（**不改写**，宁可报未命中，不得把好票号改坏）。
    典型修正：HIXCFZGYAT260042 → HMXCFZGYAT260042（小图 OCR 前缀错读）
    """
    m = re.match(r'^([A-Z][A-Z0-9]*?)(\d{3,})((?:-\d+){0,2})$', norm_dash(token))
    if not m:
        return None
    alpha, digits, suffix = m.group(1), m.group(2), (m.group(3) or '')
    best, best_score = None, 0.0
    for n in names:
        for mm in re.finditer(r'([A-Z]{2,}[A-Z0-9]*?)(\d{3,})((?:-\d+){0,2})', norm_dash(n).upper()):
            if mm.group(2) != digits:
                continue
            if (mm.group(3) or '') != suffix:
                continue
            cand_alpha = mm.group(1)
            score = difflib.SequenceMatcher(None, alpha, cand_alpha).ratio()
            if score > best_score:
                best, best_score = cand_alpha + digits + suffix, score
    t0 = norm_dash(token)
    if best and best != t0 and best_score >= 0.6:
        return best
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inputs', nargs='+', required=True)
    ap.add_argument('--out', default=None)
    ap.add_argument('--rm', default=None, help='RM-Database 目录（用于 OCR 前缀反向校正 + 命中校验）')
    ap.add_argument('--loose', action='store_true', help='放宽前缀白名单')
    ap.add_argument('--ocr-fix', dest='ocr_fix', action='store_true', default=True)
    ap.add_argument('--no-ocr-fix', dest='ocr_fix', action='store_false')
    a = ap.parse_args()

    raw, per_src = [], {}
    for p in a.inputs:
        if not os.path.exists(p):
            print('  [ERROR] 不存在: %s' % p, file=sys.stderr)
            continue
        txt = text_from_file(p)
        tks = tokens_from_text(txt, loose=a.loose)
        per_src[p] = tks
        raw.extend(tks)
    # 去重保序
    seen, ordered = set(), []
    for t in raw:
        if t not in seen:
            seen.add(t)
            ordered.append(t)

    names = rm_dir_names(a.rm) if a.rm else []
    fixed, unmatched = [], []
    for t in ordered:
        t2 = t
        if names:
            if not match_in_rm(t, names) and a.ocr_fix:
                c = ocr_fix(t, names)
                if c:
                    t2 = c
            if not match_in_rm(t2, names):
                unmatched.append(t2)
        fixed.append(t2)
    # 校正后再去重保序
    seen2, final = set(), []
    for t in fixed:
        if t not in seen2:
            seen2.add(t)
            final.append(t)

    print('=== 输入源 ===', file=sys.stderr)
    for p, tks in per_src.items():
        print('  %-60s %d 个 token' % (os.path.basename(p), len(tks)), file=sys.stderr)
    print('=== 票号清单（去重保序）%d 个 ===' % len(final), file=sys.stderr)
    for t in final:
        print('  %s' % t, file=sys.stderr)
    if names:
        print('=== RM 未命中 %d 个（Outcome1 将备注「未匹配」）===' % len(unmatched), file=sys.stderr)
        for t in unmatched:
            print('  %s' % t, file=sys.stderr)

    out = a.out or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'loan-materials-2026',
        'l1_from_input.txt')
    out = os.path.abspath(out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(final) + '\n')
    print('票号清单已写入: %s' % out, file=sys.stderr)
    # stdout 只输出票号，便于管道直传运行器
    print('\n'.join(final))


if __name__ == '__main__':
    main()
