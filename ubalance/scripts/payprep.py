#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""payprep.py — Payment 批次产出统一入口（命名方案 A · 单脚本双子命令）

Daryl 2026-10-07 定：
  · 脚本命名 = 方案 A → `payprep.py to-bank | to-misa`
  · 输出文件名一律英文，日期为**批次日期** <YYYYMMDD>：
      (a) to-bank →  Payment request to Bank-<YYYYMMDD>.xlsx
      (b) to-misa →  Payment record for MISA-<YYYYMMDD>.xlsx
  （旧名 `Payment核销测试0904-*.xlsx` / `MISA导入-*.xlsx` 作废，不再产出）
  · 批次日期省略时从「明细表 / 模板」文件名推断（如 `9-15华特明细` → 20260915、`10-5华特明细` → 20261005）

定位（零账套绑定）：本脚本**只产出文件**，不登录 MISA、不碰任何账套。
  导入（Nhập khẩu chứng từ）与核销（Đối trừ chứng từ）由知道账套的会计在 MISA 内执行。

输出格式规范（Daryl 2026-10-07 定，写入 workflow，两份产物都适用）：
  ① 字体全部 **Times New Roman**  ② **全部加框线**（细实线）  ③ **取消 wrap text**（不自动换行）
  ④ 发票日期 / payment date 一律 **MM/DD/YYYY**
  ⑤ S 列 = **文件夹号**（回溯原件）；T 列 = 税号；备注列在最后
  → 由 `payment_recon_finalize.py` / `misa_import_gen.py` 末尾统一套用；`--no-style` 可跳过（仅 finalize 支持）

薄适配层：逻辑仍留在原脚本，本脚本只做调度 + 命名，便于单点维护：
  gen_payment_recon_v2.py    明细 + 附件包（递归、发票优先）+ OCR → 送银行底稿
  fill_bank_receipt.py       （可选）银行放款回单 → 放款账号 / 日期 / Loan / VTB
  fill_payment_paid.py       （可选）电汇凭单 → 已付金额 I/J（组级/发票号/金额三路匹配）
  payment_recon_finalize.py  摘要静态化 + 删列 + 日期格式 + 格式规范
  misa_import_gen.py         定稿表 + 发票 PDF → MISA 40 列导入文件

用法：
  # (a) 送银行
  python3 scripts/payprep.py to-bank \
      --template <模板.xlsx> --detail <明细.xlsx> --attach <附件包根目录> \
      --outdir work/Mai岗位效率优化专案/out [--date 20261005] [--drop 款项类别] \
      [--receipt <回单.pdf>] [--wire <电汇凭单.pdf>] [--map-folder-by amount|order]

  # (b) MISA 入账（src 通常 = 上一步 (a) 的产物）
  python3 scripts/payprep.py to-misa \
      --src "out/Payment request to Bank-20261005.xlsx" \
      --invoices <发票目录> --outdir work/Mai岗位效率优化专案/out
"""
import argparse
import datetime as _dt
import importlib
import json
import logging
import os
import re
import sys
import warnings

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

NAME_BANK = 'Payment request to Bank-{d}.xlsx'
NAME_BANK_FX = 'Payment request to Bank-{d}-nonVND.xlsx'
NAME_LEDGER = 'Payment recon ledger-{d}.xlsx'
NAME_MISA = 'Payment record for MISA-{d}.xlsx'
NAME_BANK_FX = 'Payment request to Bank-{d}-nonVND.xlsx'

# 屏蔽 pdfminer / pypdf 噪声（G3）；行缓冲便于看进度
logging.getLogger('pdfminer').setLevel(logging.ERROR)
logging.getLogger('PIL').setLevel(logging.ERROR)
warnings.filterwarnings('ignore')
try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass


class _Tee:
    """stdout + 进度日志文件双写（G3：进度写行缓冲文件）"""

    def __init__(self, *fs):
        self.fs = fs

    def write(self, s):
        for f in self.fs:
            try:
                f.write(s)
                f.flush()
            except Exception:
                pass
        return len(s)

    def flush(self):
        for f in self.fs:
            try:
                f.flush()
            except Exception:
                pass

    def isatty(self):
        return False


def unique_out(path, rev=None):
    """Q9：目标已存在 → **自动递增** `-rN`（不静默覆盖）；`--rev N` 显式指定 rN。"""
    d, b = os.path.split(path)
    stem, ext = os.path.splitext(b)
    if rev:
        return os.path.join(d, '%s-r%d%s' % (stem, int(rev), ext))
    if not os.path.exists(path):
        return path
    n = 2
    while os.path.exists(os.path.join(d, '%s-r%d%s' % (stem, n, ext))):
        n += 1
    return os.path.join(d, '%s-r%d%s' % (stem, n, ext))


# ───────────────────────────── 工具 ─────────────────────────────
def _year():
    return _dt.date.today().year


def resolve_date(explicit, *hints):
    """返回 8 位批次日期 YYYYMMDD。explicit 优先；否则从文件名推断。"""
    if explicit:
        d = re.sub(r'\D', '', str(explicit))
        if len(d) == 8:
            return d
        if len(d) == 4:                       # MMDD
            return f'{_year()}{d}'
        raise SystemExit(f'❌ --date 需为 YYYYMMDD 或 MMDD，收到: {explicit}')

    for h in hints:
        if not h:
            continue
        b = os.path.basename(str(h))
        m = re.search(r'(20\d{2})[-_.]?(\d{2})(\d{2})', b)          # 20261005
        if m:
            return m.group(1) + m.group(2) + m.group(3)
        m = re.search(r'(?<!\d)(\d{1,2})[-_.](\d{1,2})(?!\d)', b)   # 10-5
        if m:
            mm, dd = int(m.group(1)), int(m.group(2))
            if 1 <= mm <= 12 and 1 <= dd <= 31:
                return f'{_year()}{mm:02d}{dd:02d}'
        m = re.search(r'(?<!\d)(\d{2})(\d{2})(?!\d)', b)            # 1005
        if m:
            mm, dd = int(m.group(1)), int(m.group(2))
            if 1 <= mm <= 12 and 1 <= dd <= 31:
                return f'{_year()}{mm:02d}{dd:02d}'
    raise SystemExit('❌ 无法从文件名推断批次日期 → 请显式传 --date YYYYMMDD')


def call(mod_name, argv):
    """以 sys.argv 调起既有脚本的 main()（保留原逻辑，零重写）。"""
    mod = importlib.import_module(mod_name)
    old = sys.argv
    sys.argv = [mod_name] + [str(x) for x in argv]
    try:
        mod.main()
    finally:
        sys.argv = old


def _drop(path):
    try:
        os.remove(path)
    except OSError:
        pass


def detail_currency(path):
    """明细表『原币币种』多数决 → VND / USD（混合批次取多数；单行原币以明细表为准）"""
    try:
        g = importlib.import_module('gen_payment_recon_v2')
        rows = g.load_detail(path)
    except Exception:
        return None
    votes = {}
    for r in rows:
        cur = str(r.get('cur') or '')
        u = cur.upper()
        if 'USD' in u or '美元' in cur or 'DOLLAR' in u:
            k = 'USD'
        elif 'VND' in u or '越南盾' in cur or cur.endswith('盾'):
            k = 'VND'
        else:
            k = None
        if k:
            votes[k] = votes.get(k, 0) + 1
    return max(votes, key=votes.get) if votes else None


# ───────────────────── 非 VND 表（Q5） ─────────────────────
def build_nonvnd(template, rows, out, date):
    """用同一模板另出一个非 VND 表（Q5：不同表，避免合计口径混乱）。
    rows 来自 gen_payment_recon_v2 写的 .recon.json 的 nonvnd 字段。"""
    import openpyxl
    wb = openpyxl.load_workbook(template)
    ws = wb[wb.sheetnames[0]]
    hdr = 2
    for r in range(1, min(ws.max_row, 6) + 1):
        vals = [str(ws.cell(r, c).value or '').strip() for c in range(1, ws.max_column + 1)]
        if 'STT' in vals or any('Tên khách hàng' in v for v in vals):
            hdr = r
            break
    col = {}
    for c in range(1, ws.max_column + 1):
        v = ws.cell(hdr, c).value
        if v:
            col[str(v).strip()] = c
    def C(n, d):
        return col.get(n, d)
    cB, cC, cD = C('STT', 2), C('Tên khách hàng', 3), C('Ngân hàng', 4)
    cE, cF, cG = C('Số tài khoản', 5), C('Chứng từ giải ngân', 6), C('Ngày hóa đơn', 7)
    cH = 8
    for c in range(1, ws.max_column + 1):
        v = ws.cell(hdr, c).value
        if v and str(v).startswith('Số tiền trên hóa đơn'):
            cH = c
            break
    cO, cR = C('Tiếng việt', 15), C('请款单号', 18)
    cFolder, cT = C('文件夹号', 20), C('税号', 21)
    cNote = None
    for c in range(1, ws.max_column + 1):
        v = ws.cell(hdr, c).value
        if v and str(v).strip() in ('备注', 'Ghi chú', 'Ghi chu', 'Note', 'Lý do'):
            cNote = c
            break
    if not cNote:
        from openpyxl.styles import Font as _Font
        cNote = ws.max_column + 1
        ws.cell(hdr, cNote, '备注').font = _Font(bold=True)
    def put(r, c, v):
        if c and v not in (None, ''):
            ws.cell(r, c, v)
    r = hdr + 1
    for i, row in enumerate(rows):
        put(r, cB, i + 1)
        put(r, cC, row.get('payee'))
        put(r, cD, row.get('bank'))
        put(r, cE, row.get('acct'))
        put(r, cF, row.get('no'))
        put(r, cG, row.get('date'))
        # H = 原币（发票/合同金额）；VND 等值 + 币别 + 汇率写备注（口径：H 定义 = 发票金额）
        _vnd = int(row.get('amount') or 0)
        _orig = row.get('orig_amount')
        ws.cell(r, cH, int(_orig) if _orig not in (None, '') else _vnd)
        put(r, cO, row.get('payee'))
        put(r, cR, row.get('oa'))
        put(r, cFolder, row.get('folder'))
        put(r, cT, row.get('tax'))
        _cur = row.get('currency') or ''
        _parts = []
        if _cur:
            _parts.append('Loại tiền: %s' % _cur)
        if _orig not in (None, '') and _vnd:
            # 双口径写明：原币金额 + 本币（VND）等值；数字用千分位逗号，便于机器核对/检索
            _parts.append('Nguyên tệ %s %s | Tương đương %s VND%s' % (
                format(int(_orig), ','), _cur.split()[-1] if _cur else '',
                format(_vnd, ','),
                (' (tỷ giá %s)' % format(int(row.get('rate')), ',')) if row.get('rate') else ''))
        elif _vnd:
            _parts.append('本币付款金额 %s VND (theo bảng kê)' % format(_vnd, ','))
        if row.get('note'):
            _parts.append(row.get('note'))
        put(r, cNote, ' | '.join(_parts))
        r += 1
    if ws.max_row > r - 1:
        ws.delete_rows(r, ws.max_row - r + 1)
    # H 列表头：原币（混合币别批次，逐行看备注币别）
    for c in range(1, ws.max_column + 1):
        v = ws.cell(hdr, c).value
        if v and re.match(r'^Số tiền trên hóa đơn/\s*Hợp đồng', str(v)):
            ws.cell(hdr, c, 'Số tiền trên hóa đơn/ Hợp đồng (Ngoại tệ / 原币)')
            break
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    wb.save(out)
    return out


# ───────────────────────── (a) 送银行 ─────────────────────────
def cmd_to_bank(a):
    outdir = os.path.abspath(a.outdir)
    os.makedirs(outdir, exist_ok=True)
    date = resolve_date(a.date, a.detail, a.template)
    logf = open(os.path.join(outdir, 'payprep-log-%s.txt' % date), 'w', encoding='utf-8')
    _orig_stdout = sys.stdout
    sys.stdout = _Tee(_orig_stdout, logf)
    try:
        return _to_bank_inner(a, outdir, date)
    finally:
        sys.stdout = _orig_stdout
        logf.close()


def _to_bank_inner(a, outdir, date):
    final = unique_out(os.path.join(outdir, NAME_BANK.format(d=date)), a.rev)
    print(f'=== payprep to-bank | 批次 {date} | 输出 {os.path.basename(final)} ===')
    ccy = (a.currency or detail_currency(a.detail) or '').upper() or None
    print(f'  币别（H 列表头）: {ccy or "(自动推断)"}')

    tmp = os.path.join(outdir, '._payprep_1.xlsx')
    call('gen_payment_recon_v2', [
        '--template', a.template, '--detail', a.detail, '--attach', a.attach,
        '--out', tmp, '--map-folder-by', a.map_folder_by,
    ])
    cur, temps = tmp, [tmp]

    if a.receipt:
        nxt = os.path.join(outdir, '._payprep_2.xlsx')
        argv = ['--xlsx', cur, '--receipt', a.receipt, '--out', nxt]
        if a.set_bank:
            argv += ['--set-bank', a.set_bank]
        if a.set_method:
            argv += ['--set-method', a.set_method]
        argv += ['--summary-lang', a.summary_lang]
        print('\n=== 回单回填 ===')
        call('fill_bank_receipt', argv)
        cur = nxt
        temps.append(nxt)

    if a.wire:
        nxt = os.path.join(outdir, '._payprep_3.xlsx')
        argv = ['--xlsx', cur, '--wire', a.wire, '--out', nxt, '--fill-i', '--fill-j']
        print('\n=== 电汇凭单回填 ===')
        call('fill_payment_paid', argv)
        cur = nxt
        temps.append(nxt)

    argv = ['--xlsx', cur, '--out', final, '--summary-lang', a.summary_lang]
    if ccy:
        argv += ['--currency', ccy]
    if not a.no_submit:
        argv += ['--submit']            # Q7：提交版净化（K/L 空 → 摘要留空）
    for col in a.drop:
        argv += ['--drop', col]
    print('\n=== 收尾（摘要静态化/净化 + 日期格式 + 删列 + 格式规范） ===')
    call('payment_recon_finalize', argv)

    # ── Q5：非 VND 表（仅当存在非 VND 明细/发票）──
    fx_out = None
    side_path = tmp + '.recon.json'
    try:
        with open(side_path, encoding='utf-8') as f:
            side = json.load(f)
        fx_rows = side.get('nonvnd') or []
        if fx_rows:
            fx_out = unique_out(os.path.join(outdir, NAME_BANK_FX.format(d=date)), a.rev)
            build_nonvnd(a.template, fx_rows, fx_out, date)
            call('payment_recon_finalize', ['--xlsx', fx_out, '--out', fx_out,
                                            '--submit', '--hdr-currency', 'Ngoại tệ / 原币'])
            print('\n✅ (a-fx) %s（%d 行非 VND）' % (fx_out, len(fx_rows)))
    except FileNotFoundError:
        pass
    except Exception as ex:
        print('  [warn] 非 VND 表产出失败: %s' % ex)

    # ── 台账 sidecar 随交付件同名落地（D3/F2）──
    ledger_out = None
    try:
        os.replace(side_path, final + '.recon.json')
    except OSError:
        pass

    # ── 发票级对账台账 xlsx（D3/F2，recon_ledger.py）──
    if os.path.exists(final + '.recon.json'):
        try:
            ledger_out = unique_out(os.path.join(outdir, NAME_LEDGER.format(d=date)), a.rev)
            call('recon_ledger', ['--json', final + '.recon.json', '--out', ledger_out])
            print('\n✅ (a-ledger) %s' % ledger_out)
        except Exception as ex:
            print('  [warn] 台账产出失败: %s' % ex)

    for t in temps:
        if os.path.exists(t + '.recon.txt'):
            try:
                # 报告标题写成**交付件名**（原为中间临时名 ._payprep_1.xlsx，对账时易误认）
                _txt = open(t + '.recon.txt', encoding='utf-8').read()
                _txt = _txt.replace('# Reconcile report · %s' % os.path.basename(t),
                                   '# Reconcile report · %s' % os.path.basename(final), 1)
                open(final + '.recon.txt', 'w', encoding='utf-8').write(_txt)
            except OSError:
                pass
        _drop(t)
    print(f'\n✅ (a) {final}')
    if fx_out:
        print(f'✅ (a-fx) {fx_out}')
    if ledger_out:
        print(f'✅ (a-ledger) {ledger_out}')
    return final


# ───────────────────────── (b) MISA ─────────────────────────
def cmd_to_misa(a):
    outdir = os.path.abspath(a.outdir)
    os.makedirs(outdir, exist_ok=True)
    date = resolve_date(a.date, a.src)
    final = os.path.join(outdir, NAME_MISA.format(d=date))
    print(f'=== payprep to-misa | 批次 {date} | 输出 {os.path.basename(final)} ===')

    # 列映射自检：misa_import_gen 按固定列号取值（发票号 F=6 / 价税合计 H=8 /
    # 请款单号=17 / 凭证摘要=18 / 税号=19）→ 与 to-bank 产物（含删列后）对齐
    try:
        import openpyxl
        ws = openpyxl.load_workbook(a.src).active
        hdr = {c: ws.cell(2, c).value for c in (6, 8, 17, 18, 19)}
        print('  列映射自检:', hdr)
        if not ws.cell(2, 6).value or not ws.cell(2, 8).value:
            raise SystemExit('❌ 定稿表列 6/8 为空 → 不是期望的 Payment 定稿表结构')
    except ImportError:
        pass

    call('misa_import_gen', [
        '--src', a.src, '--invoices', a.invoices, '--out', final,
        '--date', date,
    ] + (['--currency', a.currency] if a.currency else []))
    print(f'\n✅ (b) {final}')
    return final


# ───────────────────────────── main ─────────────────────────────
def main():
    ap = argparse.ArgumentParser(description='Payment 批次产出统一入口（命名方案 A）')
    sub = ap.add_subparsers(dest='cmd', required=True)

    b = sub.add_parser('to-bank', help='生成送银行文件')
    b.add_argument('--template', required=True)
    b.add_argument('--detail', required=True)
    b.add_argument('--attach', required=True, help='附件包根目录（含 1/2/3… 子文件夹）')
    b.add_argument('--outdir', required=True)
    b.add_argument('--date', default=None, help='批次日期 YYYYMMDD（省略则从文件名推断）')
    b.add_argument('--drop', action='append', default=[], help='收尾时整列删除（表头名或列字母），可重复')
    b.add_argument('--receipt', default=None, help='银行放款回单 PDF（可选）')
    b.add_argument('--wire', default=None, help='电汇凭单 PDF（可选）')
    b.add_argument('--set-bank', default=None)
    b.add_argument('--set-method', default=None)
    b.add_argument('--map-folder-by', choices=['amount', 'order'], default='amount')
    b.add_argument('--summary-lang', choices=['vi', 'zh'], default='vi', help='凭证摘要语言；默认 vi')
    b.add_argument('--currency', choices=['VND', 'USD'], default=None, help='H 列表头/金额币别；默认从明细表推断')
    b.add_argument('--rev', type=int, default=None, help='修版号（Q9）：输出 ...-rN.xlsx；不传则重名时自动 r2/r3…')
    b.add_argument('--no-submit', action='store_true', help='关闭提交版净化（保留摘要占位符公式，仅内部草稿用）')
    b.set_defaults(func=cmd_to_bank)

    m = sub.add_parser('to-misa', help='生成 MISA 导入文件')
    m.add_argument('--src', required=True, help='定稿表（通常 = to-bank 的产物）')
    m.add_argument('--invoices', required=True, help='发票 PDF 目录')
    m.add_argument('--outdir', required=True)
    m.add_argument('--date', default=None)
    m.add_argument('--currency', choices=['VND', 'USD'], default=None, help='Loại tiền；默认从定稿表 H 列表头推断')
    m.set_defaults(func=cmd_to_misa)

    a = ap.parse_args()
    try:
        a.func(a)
    except SystemExit:
        raise
    except Exception as ex:
        import traceback
        traceback.print_exc()
        print('❌ payprep 失败: %s' % ex, file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
