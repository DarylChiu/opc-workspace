#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""regress_invoices.py — 越南发票解析回归（C8 / 验收 §2-1）

两套样本（均为**只读复制**，原包未改；多票文件样本由两张真发票 pdfunite 合成并已标注）：

  A) `tests/fixtures/invoices/expected.json`  —— 16 样本（凭证-20261008 + 凭证-0915）
     覆盖：短号(4/57/65/78/245/299/521)、前导 0(00000223/00000235/00000129/00000090/00001044/00003411/00022388)、
     水印型、扫描件（无文本层→页眉定向 OCR）、调整票/贷项（负数）、INTERTEK 版式、**多票文件**（一个 PDF 两张票）
  B) `scripts/fixtures/invoices/expected.json` —— 15 样本（含序列号 Ký hiệu 与号码来源 num_src 断言）
     + 卷级用例 `cases/folder16_multi`（多文件同卷 3 张票合计）

断言：发票号（**含前导 0 原样**）/ 日期 / 金额 / 税号 / 序列号 / 调整票标记 / 号码来源
结构断言：解析器**不存在补零入口**（`pad_inv_no` 已整函数删除）；号码来源 ∈ {body, ocr-header, filename}

用法：`bash scripts/regress_invoices.sh`（任一条失败 → 非 0 退出并打印差异）
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
SUITES = [
    (os.path.join('tests', 'fixtures', 'invoices', 'expected.json'), 'A · 1005+0915 样本'),
    (os.path.join('scripts', 'fixtures', 'invoices', 'expected.json'), 'B · 版式/序列号样本'),
]


def _num(x):
    """带符号数字（⚠ 负数金额必须保留负号：调整票/贷项通知单）"""
    s = str(x if x is not None else '').strip()
    neg = s.startswith('-') or s.startswith('−')
    d = ''.join(ch for ch in s if ch.isdigit())
    if not d:
        return 0
    v = int(d)
    return -v if neg else v


def check_one(V, V_dir, case, fails, ok):
    fn = case['file']
    path = os.path.join(V_dir, fn)
    if not os.path.exists(path):
        fails.append('❌ 缺样本文件：%s' % fn)
        return
    try:
        invs = V.parse_pdf(path)
    except Exception as ex:                       # noqa: BLE001
        fails.append('❌ %s → 解析异常 %r' % (fn, ex))
        return
    if not invs:
        fails.append('❌ %s → 未解析出发票' % fn)
        return
    if case.get('multi_invoice') is not None and len(invs) != case['multi_invoice']:
        fails.append('❌ %s → 期望 %d 张发票，实际 %d 张' % (fn, case['multi_invoice'], len(invs)))
        return
    idx = case.get('index', 0) or 0
    if idx >= len(invs):
        fails.append('❌ %s → 缺少索引 %d' % (fn, idx))
        return
    inv = invs[idx]

    bad = []
    got_no = str(inv.get('invoice_number') or '')
    if 'no' in case and got_no != case['no']:
        # 允许显式声明的兜底值（但仍必须带「待核」标记）
        if case.get('alt_no') and got_no == case['alt_no'] and inv.get('_need_check_no'):
            pass
        else:
            bad.append('发票号 期望 %r 实际 %r' % (case['no'], got_no))
    if 'date' in case and str(inv.get('invoice_date') or '') != case['date']:
        bad.append('日期 期望 %r 实际 %r' % (case['date'], inv.get('invoice_date')))
    if 'amount' in case:
        want = int(case['amount'])
        got = _num(inv.get('total_amount'))
        cands = [_num(c) for c in (inv.get('_cands') or [])]
        if case.get('amount_mode', 'exact') == 'candidate':
            if want not in cands:
                bad.append('金额 期望候选含 %s 实际候选 %s' % (want, cands))
        elif got != want:
            bad.append('金额 期望 %s 实际 %s（候选 %s）' % (want, got, cands))
    if 'tax' in case and str(inv.get('vendor_tax_code') or '') != str(case['tax']):
        bad.append('税号 期望 %r 实际 %r' % (case['tax'], inv.get('vendor_tax_code')))
    if 'serial' in case and str(inv.get('invoice_serial') or '').upper() != str(case['serial']).upper():
        bad.append('序列号 期望 %r 实际 %r' % (case['serial'], inv.get('invoice_serial')))
    if case.get('adjust') is not None:
        got = bool(inv.get('_adjust')) or _num(inv.get('total_amount')) < 0
        if got != bool(case['adjust']):
            bad.append('调整票标记 期望 %r 实际 %r' % (case['adjust'], got))
    if 'num_src' in case and str(inv.get('_num_src') or '') != case['num_src']:
        bad.append('号码来源 期望 %r 实际 %r' % (case['num_src'], inv.get('_num_src')))
    src = str(inv.get('_num_src') or '')
    if src not in ('body', 'ocr-header', 'filename'):
        bad.append('号码来源 %r 不在 {body,ocr-header,filename}' % src)

    if bad:
        fails.append('❌ %-44s %s' % (fn[:44], ' ; '.join(bad)))
    else:
        ok.append(1)
        tag = ','.join(case.get('tags') or [])[:38]
        print('✅ %-44s no=%-11s date=%-10s amt=%-15s tax=%-11s %s' % (
            fn[:44], got_no or '-', inv.get('invoice_date') or '-',
            format(_num(inv.get('total_amount')), ','), inv.get('vendor_tax_code') or '-', tag))


def check_folder(V, base, case, fails, ok):
    """卷级用例：一个目录多张发票 → 逐票金额 + 合计（目录相对样本集根或其上一级皆可）"""
    import glob
    cands = [os.path.join(base, case['dir']),
             os.path.join(os.path.dirname(base.rstrip(os.sep)), case['dir'])]
    d = next((c for c in cands if os.path.isdir(c)), cands[0])
    files = sorted(f for f in glob.glob(os.path.join(d, '**', '*'), recursive=True)
                   if os.path.splitext(f)[1].lower() in ('.pdf', '.jpg', '.jpeg', '.png', '.tif', '.tiff'))
    if not files:
        fails.append('❌ 卷级用例 %s → 目录无样本文件（%s）' % (case['name'], d))
        return
    got, errs = {}, []
    for f in files:
        try:
            for iv in V.parse_pdf(f):
                no = str(iv.get('invoice_number') or '')
                if no:
                    got[no] = _num(iv.get('total_amount'))
        except Exception as ex:                  # noqa: BLE001
            errs.append('%s → %r' % (os.path.basename(f), ex))
    want = {str(k): _num(v) for k, v in case['invoices'].items()}
    bad = []
    if errs:
        bad.append('解析异常 %s' % ' ; '.join(errs))
    for no, amt in want.items():
        if got.get(no) != amt:
            bad.append('发票 %s 期望 %s 实际 %s' % (no, amt, got.get(no)))
    if sum(got.values()) != _num(case['sum']):
        bad.append('合计 期望 %s 实际 %s' % (_num(case['sum']), sum(got.values())))
    if bad:
        fails.append('❌ 卷级用例 %s → %s' % (case['name'], ' ; '.join(bad)))
    else:
        ok.append(1)
        print('✅ 卷级用例 %-30s %d 张票 合计=%s' % (case['name'], len(got), format(sum(got.values()), ',')))


def main():
    import logging
    logging.getLogger('pdfminer').setLevel(logging.ERROR)
    sys.path.insert(0, HERE)
    import vn_invoice_parse as V

    fails, ok = [], []

    # ── 结构断言：不得存在补零函数（Daryl 16:2x 口径）──
    if hasattr(V, 'pad_inv_no'):
        fails.append('❌ 结构断言：vn_invoice_parse 仍存在 pad_inv_no（禁止任何补零路径）')
    else:
        ok.append(1)
        print('✅ 结构断言：无 pad_inv_no（不臆造位数 / 不补 0）')

    for rel, label in SUITES:
        spec_path = os.path.join(ROOT, rel)
        if not os.path.exists(spec_path):
            print('⚠️ 跳过缺席样本集 %s' % rel)
            continue
        spec = json.load(open(spec_path, encoding='utf-8'))
        base = os.path.dirname(spec_path)
        samples = spec.get('samples') or [c for c in (spec.get('cases') or []) if c.get('file')]
        folders = [c for c in (spec.get('cases') or []) if c.get('dir')]
        print('\n── 样本集 %s（%s）—— %d 张票%s' % (label, rel, len(samples),
                                                ' + %d 卷级用例' % len(folders) if folders else ''))
        for case in samples:
            check_one(V, base, case, fails, ok)
        for case in folders:
            check_folder(V, base, case, fails, ok)

    print('\n%s' % ('─' * 74))
    if fails:
        print('回归失败 %d 项 / 通过 %d 项：' % (len(fails), len(ok)))
        for x in fails:
            print('  ' + x)
        return 1
    print('✅ 回归全绿：%d/%d 项通过（发票号含前导 0 / 日期 / 金额 / 税号 / 序列号 / 调整票 / 号码来源）'
          % (len(ok), len(ok)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
