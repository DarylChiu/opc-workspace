#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""summary_text.py — 凭证摘要（Diễn giải）文本生成 · 单一事实源

Daryl 2026-10-07 定：摘要内容用**越南语**（会贴进 MISA 的 Diễn giải）。
英文/中文仅作兼容保留（--summary-lang zh）。

越南语格式：
  Tại TK <放款账号> ngày <dd/mm/yyyy> giải ngân theo OA <请款单号> của <供应商越文名> - HĐ số <发票号> - <1.451.652.058> VND
中文格式（旧口径，兼容）：
  在<账号>账号于<M月D日>放款OA流程号<OA>的<供应商越文名>发票号<发票号>金额<金额>vnd
"""
import datetime
import re

DEFAULTS = {'acct': '{放款账号}', 'date': '{放款日期}', 'oa': '{OA流程号}'}


def _num(v):
    if v is None or v == '':
        return ''
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return re.sub(r'[^0-9]', '', str(v))


def fmt_vnd(v):
    """越南式千分位：1451652058 → 1.451.652.058"""
    d = _num(v)
    return re.sub(r'\B(?=(\d{3})+(?!\d))', '.', d) if d else ''


def date_txt(v, lang='vi'):
    dt = None
    if isinstance(v, (datetime.date, datetime.datetime)):
        dt = v
    else:
        s = str(v or '').strip()
        m = re.match(r'^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})', s)
        if m:
            dt = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    if dt is None:
        return str(v or '').strip() or DEFAULTS['date']
    return dt.strftime('%d/%m/%Y') if lang == 'vi' else f'{dt.month}月{dt.day}日'


def build(lang, acct, date_val, oa, vendor, inv, amt):
    """按语言拼一段摘要；缺账号/日期时保留占位符（便于人工识别待回填）。"""
    lang = (lang or 'vi').lower()
    acct = str(acct or '').strip() or DEFAULTS['acct']
    oa = str(oa or '').strip() or DEFAULTS['oa']
    vendor = str(vendor or '').strip()
    inv = str(inv or '').strip()
    if lang.startswith('vi'):
        return (f'Tại TK {acct} ngày {date_txt(date_val, "vi")} giải ngân theo OA {oa} '
                f'của {vendor} - HĐ số {inv} - {fmt_vnd(amt)} VND')
    return (f'在{acct}账号于{date_txt(date_val, "zh")}放款OA流程号{oa}的{vendor}'
            f'发票号{inv}金额{_num(amt)}vnd')


if __name__ == '__main__':
    print(build('vi', '806008129612', '2026-09-04', 'YNDGBX202608240550',
                'CÔNG TY CỔ PHẦN NEWTECH LOGISTICS', '00000017', 1451652058))
    print(build('zh', None, None, None, 'CONG TY A', '00000017', 1451652058))
