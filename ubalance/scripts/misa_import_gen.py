#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""misa_import_gen.py — 生成 MISA AMIS「Phiếu chi tiền gửi đa tiền tệ」导入文件

输入:
  --src   定稿表（如 Payment核销测试0904-5.xlsx）
  --invoices  发票 PDF 目录（用于抽 未税/税率/税额/MST，文件名为含发票号）
  --out   输出 xlsx（40 列模板格式，表头照抄 MISA 官方模板第 8 行）

⚠️ 顶部 CFG 里的「暂定值」= 需客户会计政策/字典确认的字段，确认后改这里重跑即可。
"""
import os, re, glob, argparse, datetime
import pdfplumber
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

# ───────────────────────── 暂定值（待会计/字典确认）─────────────────────────
CFG = {
    'phuong_thuc_tt': 'Ủy nhiệm chi',
    'ly_do_chi': 'Chi mua ngoài có hóa đơn',      # 字典值待确认
    'tk_no': '331',                               # ← 会计政策待确认
    'tk_co': '1121',                              # ← 会计政策待确认（放款虚拟账号对应的银行科目）
    'tk_thue': '1331',                            # ← 会计政策待确认
    'nhom_hhdv': 1,                               # ← 字典值待确认
    'so_ct_fmt': 'UNC0904-{n}',                   # ← 凭证字号规则待确认
    'bank_name': 'Ngân hàng TMCP Công thương Việt Nam - CN Nhơn Trạch',  # ← 全称待确认
}
HEADERS = ['Phương thức thanh toán','Ngày hạch toán (*)','Ngày chứng từ (*)','Số chứng từ (*)','Lý do chi',
 'Là UNC chuyển tiền theo lô','Nội dung thanh toán','Số tài khoản chi','Tên ngân hàng chi ','Mã đối tượng ',
 'Tên đối tượng','Số tài khoản nhận','Tên ngân hàng nhận','Loại tiền','Tỷ giá','Diễn giải (hạch toán)',
 'TK Nợ (*)','TK Có (*)','Số tiền','Số tiền quy đổi','Tên người hưởng','TK hưởng','Tên NH thụ hưởng',
 'Tên chi nhánh NH thụ hưởng','Mã đối tượng (hạch toán)','Hạch toán gộp nhiều hóa đơn','Diễn giải thuế',
 'Có hóa đơn','Giá trị HHDV chưa thuế','% thuế GTGT','% thuế suất KHAC','Tiền thuế GTGT',
 'Tiền thuế GTGT quy đổi','TK thuế GTGT','Ngày hóa đơn','Số hóa đơn','Nhóm HHDV mua vào','Mã NCC',
 'Tên NCC','Mã số thuế NCC']


def norm_digits(s):
    return re.sub(r'[^0-9]', '', s or '')


def _amt(blob, labels):
    r"""按标签找金额：优先越南式千分位（179.663.201），兜底长数字串。
    注意水印碎数字会散落在数字后面 → 不能用 [\d.\s]+ 贪婪匹配。"""
    for lab in labels:
        L = re.escape(lab)
        for pat in (L + r'[^\d]{0,40}(\d{1,3}(?:\.\d{3})+)',
                    L + r'[^\d]{0,40}(\d{6,})'):
            m = re.search(pat, blob)
            if m:
                return norm_digits(m.group(1))
    return None


def parse_invoice(path):
    """从发票 PDF 抽: mst / 未税 / 税率 / 税额 / 合计 / 日期"""
    with pdfplumber.open(path) as pdf:
        txt = "\n".join((p.extract_text() or '') for p in pdf.pages[:2])
    # 去掉水印碎字（康熙部首/部首补充区 U+2E80-U+2FFF + CJK 统一表意）
    txt = re.sub(r'[\u2e80-\u2fff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]', '', txt)
    blob = txt
    d = {}

    d['excl'] = _amt(blob, ['Cộng tiền hàng (Sub total)', 'Cộng tiền hàng(Total amount excl. VAT)', 'Cộng tiền hàng', 'Sub total'])
    d['vat'] = _amt(blob, ['Cộng tiền thuế GTGT (VAT amount)', 'Tiền thuế GTGT(VAT amount)', 'Tiền thuế GTGT'])
    d['total'] = _amt(blob, ['Tổng cộng tiền thanh toán', 'Tổng tiền thanh toán', 'Total payment'])
    m = re.search(r'(?:Thuế suất GTGT|Thuế suất GTGT \(VAT rate\)|Thuế suất GTGT \(Tax rate\))[^\d]{0,10}(\d{1,2})\s*%', blob)
    if not m:
        m = re.search(r'GTGT[^\d%]{0,20}(\d{1,2})\s*%', blob)
    if m: d['rate'] = int(m.group(1))
    # 卖方 MST：越南税号 = 10 位（可带 -xxx 分支） → 取前 10 位
    mst = re.findall(r'(?:Mã số thuế|MST)\s*[\(\[]?\s*(?:Tax\s*[Cc]ode)?\s*[\)\]]?\s*[:]?\s*([\d\s]{10,22})', blob)
    mst = [norm_digits(x)[:10] for x in mst]
    mst = [x for x in mst if len(x) == 10]
    d['mst_all'] = mst
    if mst: d['mst'] = mst[0]
    # 日期: 「Ngày 21 tháng 08 năm 2026」/「Ngày (day) 19 tháng (month) 08 năm (year) 2026」
    m = re.search(r'Ng[àa]y[^\d]{0,20}(\d{1,2})\s*th[áa]ng[^\d]{0,20}(\d{1,2})\D{0,5}n[ăa]m[^\d]{0,20}(\d{4})', blob)
    if m:
        d['date'] = f"{int(m.group(1)):02d}/{int(m.group(2)):02d}/{m.group(3)}"
    # 合计：MISA 版发票无「Tổng cộng」行 → 用「未税+税额」兜底
    if d.get('excl') and d.get('vat'):
        d.setdefault('total', str(int(d['excl']) + int(d['vat'])))
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True)
    ap.add_argument('--invoices', default='attachments/凭证')
    ap.add_argument('--out', required=True)
    ap.add_argument('--date', default=None, help='批次日期 YYYYMMDD → 决定凭证字号前缀 UNC<MMDD> 与页首批次标签')
    ap.add_argument('--currency', default=None, help="Loại tiền (VND/USD)；不传则从定稿表 H 列表头推断，推论不出默认 VND")
    a = ap.parse_args()

    # 批次日期 → 凭证字号前缀 + 页首标签（payprep.py 会传入；不传则沿用 CFG 默认）
    batch_disp = '04/09/2026'
    if a.date:
        d = re.sub(r'\D', '', str(a.date))
        if len(d) != 8:
            raise SystemExit(f'❌ --date 需为 YYYYMMDD，收到: {a.date}')
        CFG['so_ct_fmt'] = 'UNC' + d[4:] + '-{n}'
        batch_disp = f'{d[6:]}/{d[4:6]}/{d[0:4]}'

    # 币别（写入 Loại tiền 列）：显式参数 > 定稿表 H 列表头 > 默认 VND
    loai_tien = (a.currency or '').upper().strip()
    if loai_tien not in ('VND', 'USD'):
        loai_tien = 'VND'
        try:
            import openpyxl as _oxl
            _ws = _oxl.load_workbook(a.src).active
            for _c in range(1, _ws.max_column + 1):
                _v = _ws.cell(2, _c).value
                _m = re.match(r'^Số tiền trên hóa đơn/\s*Hợp đồng\s*\((VND|USD)\)', str(_v or ''), re.I)
                if _m:
                    loai_tien = _m.group(1).upper()
                    break
        except Exception:
            pass

    # 1) 读定稿表
    wb = openpyxl.load_workbook(a.src); ws = wb.active
    H = {ws.cell(2, c).value: c for c in range(1, ws.max_column + 1) if ws.cell(2, c).value}
    rows = []
    for r in range(3, ws.max_row + 1):
        inv = ws.cell(r, 6).value
        if not inv: continue
        rows.append(dict(
            stt=ws.cell(r, 2).value, vendor_en=ws.cell(r, 3).value, bank=ws.cell(r, 4).value,
            acct_recv=ws.cell(r, 5).value, inv=str(inv), inv_date=ws.cell(r, 7).value,
            gross=ws.cell(r, 8).value, vendor_vi=ws.cell(r, 15).value, oa=ws.cell(r, 17).value,
            memo=ws.cell(r, 18).value, acct_loan=ws.cell(r, 11).value,
            pay_date=ws.cell(r, 12).value, mst=ws.cell(r, 19).value,
        ))

    # 2) 发票 PDF 抽税
    pdfs = [p for p in glob.glob(os.path.join(a.invoices, '*', '*.pdf')) if 'BẢNG KÊ' not in p]
    for row in rows:
        hit = [p for p in pdfs if row['inv'] in os.path.basename(p)]
        if not hit:
            print(f"⚠️ 未找到发票文件: {row['inv']}"); continue
        d = parse_invoice(hit[0])
        row.update(excl=d.get('excl'), vat=d.get('vat'), rate=d.get('rate'), total_pdf=d.get('total'),
                   mst_pdf=d.get('mst'), inv_date_pdf=d.get('date'))
        e, v, t = int(row['excl'] or 0), int(row['vat'] or 0), int(row['gross'] or 0)
        chk = '✅' if e + v == t else f'❌ 差额{e + v - t:+,}'
        mchk = '✅' if str(row['mst_pdf']) == str(row['mst']) else f"⚠️ 定稿表税号={row['mst']}"
        print(f"  {row['inv']:>10} | 未税 {e:>15,} + 税 {v:>13,} = {e + v:>15,} vs 定稿 {t:>15,} {chk}"
              f" | {row['rate']}% | MST {row['mst_pdf']} {mchk} | {row['inv_date_pdf']}")

    # 3) 生成 MISA 导入文件
    out = openpyxl.Workbook(); o = out.active; o.title = 'Phieu chi tien gui'
    o['A1'] = f'FILE NHẬP KHẨU PHIẾU CHI TIỀN GỬI (MISA AMIS) — HUATEX · lô {batch_disp}'
    o['A1'].font = Font(bold=True, size=13)
    o['A2'] = 'Hướng dẫn: điền dữ liệu vào các cột tương ứng; cột có (*) là bắt buộc.'
    o['A3'] = '⚠️ Các ô đánh dấu [XÁC NHẬN] là giá trị tạm — chờ xác nhận chính sách kế toán / danh mục của công ty trước khi nhập chính thức.'
    thin = Side(style='thin', color='BBBBBB')
    for c, h in enumerate(HEADERS, 1):
        cell = o.cell(8, c, h)
        cell.font = Font(bold=True, size=10)
        cell.fill = PatternFill('solid', fgColor='DDEBF7' if c < 16 else 'FCE4D6')
        cell.alignment = Alignment(wrap_text=True, vertical='center')
        cell.border = Border(bottom=thin)
    o.freeze_panes = 'A9'

    for i, row in enumerate(rows, 1):
        r = 8 + i
        pd_ = row['pay_date']
        pd_s = pd_.strftime('%d/%m/%Y') if isinstance(pd_, (datetime.date, datetime.datetime)) else str(pd_)
        def _dmy(v):
            if isinstance(v, (datetime.date, datetime.datetime)):
                return v.strftime('%d/%m/%Y')
            s = str(v or '').strip()
            m = re.match(r'^(\d{4})-(\d{1,2})-(\d{1,2})', s)
            return f'{int(m.group(3)):02d}/{int(m.group(2)):02d}/{m.group(1)}' if m else s
        inv_d = row['inv_date_pdf'] or _dmy(row['inv_date'])
        bank_en = (row['bank'] or '')
        branch = bank_en.split('CHI NHANH')[-1].strip() if 'CHI NHANH' in bank_en else ''
        vals = {
            1: CFG['phuong_thuc_tt'], 2: pd_s, 3: pd_s, 4: CFG['so_ct_fmt'].format(n=row['stt']),
            5: CFG['ly_do_chi'], 6: '', 7: row['memo'], 8: row['acct_loan'], 9: CFG['bank_name'],
            10: '', 11: row['vendor_vi'], 12: row['acct_recv'], 13: bank_en, 14: loai_tien, 15: '',
            16: row['memo'], 17: CFG['tk_no'], 18: CFG['tk_co'], 19: row['gross'], 20: '',
            21: row['vendor_vi'], 22: row['acct_recv'], 23: bank_en, 24: branch, 25: '',
            26: 'Không',                        # Hạch toán gộp nhiều hóa đơn
            27: '',                             # Diễn giải thuế
            28: 'Có',                           # Có hóa đơn
            29: row['excl'],                    # Giá trị HHDV chưa thuế
            30: row['rate'],                    # % thuế GTGT
            31: '',                             # % thuế suất KHAC
            32: row['vat'],                     # Tiền thuế GTGT
            33: '',                             # Tiền thuế GTGT quy đổi
            34: CFG['tk_thue'],                 # TK thuế GTGT
            35: inv_d,                          # Ngày hóa đơn
            36: row['inv'],                     # Số hóa đơn
            37: CFG['nhom_hhdv'],               # Nhóm HHDV mua vào
            38: '',                             # Mã NCC（待 MISA 主数据）
            39: row['vendor_vi'],               # Tên NCC
            40: row['mst_pdf'] or row['mst'],   # Mã số thuế NCC
        }
        for c, v in vals.items():
            cell = o.cell(r, c, v)
            cell.alignment = Alignment(wrap_text=False, vertical='center')
    widths = {1: 16, 2: 14, 3: 14, 4: 16, 5: 22, 7: 46, 8: 16, 9: 34, 11: 40, 12: 16, 13: 42,
              16: 46, 19: 16, 21: 40, 22: 16, 23: 42, 28: 18, 31: 16, 34: 13, 35: 14, 38: 40, 39: 15}
    from openpyxl.utils import get_column_letter as gl
    for c, w in widths.items(): o.column_dimensions[gl(c)].width = w
    o.row_dimensions[1].height = 20

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)

    # ── 输出格式规范（Daryl 2026-10-07 定，已写入 workflow）:
    #    ① 字体全部 Times New Roman  ② 全部加框线  ③ 取消 wrap text
    from copy import copy as _copy
    _thin = Side(style='thin', color='000000')
    _bd = Border(left=_thin, right=_thin, top=_thin, bottom=_thin)
    for _r in range(1, o.max_row + 1):
        for _c in range(1, o.max_column + 1):
            _cell = o.cell(_r, _c)
            _f = _copy(_cell.font)
            _f.name = 'Times New Roman'
            _f.size = _f.size or 11
            _cell.font = _f
            _cell.border = _bd
            _al = _cell.alignment
            _cell.alignment = Alignment(horizontal=_al.horizontal,
                                        vertical=_al.vertical or 'center', wrap_text=False)
    print('🎨 格式规范: Times New Roman + 全框线 + 取消 wrap text（%d行×%d列）' % (o.max_row, o.max_column))

    out.save(a.out)
    s = sum(int(x['gross']) for x in rows)
    print(f"\n✅ 已生成 {len(rows)} 行 → {a.out}")
    print(f"   金额合计 {s:,} VND | 单据 {[x['inv'] for x in rows]}")


if __name__ == '__main__':
    main()
