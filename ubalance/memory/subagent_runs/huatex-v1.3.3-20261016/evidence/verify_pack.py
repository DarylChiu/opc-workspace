#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v1.3.3 交付包验收（只读 zip，不改包）。输出 JSON 摘要。"""
import hashlib
import io
import json
import os
import sys
import zipfile

ZIP = sys.argv[1]
r = {'zip': ZIP}
raw = open(ZIP, 'rb').read()
r['bytes'] = len(raw)
r['sha256'] = hashlib.sha256(raw).hexdigest()

zf = zipfile.ZipFile(io.BytesIO(raw))
r['entries'] = len(zf.infolist())
r['testzip'] = zf.testzip()  # None == OK

# UTF-8 文件名标志 0x800
miss = []
for i in zf.infolist():
    if not (i.flag_bits & 0x800):
        miss.append(i.filename)
r['utf8_missing'] = miss

ext = {}
for i in zf.infolist():
    e = os.path.splitext(i.filename)[1].lower()
    ext[e] = ext.get(e, 0) + 1
r['ext_counts'] = ext

# 内置素材逐字节
want = {
    'installers/tesseract-ocr-w64-setup-5.4.0.20240606.exe': 50175248,
    'installers/Release-26.09.0-0.zip': 43709956,
    'tessdata/eng.traineddata': 4113088,
    'tessdata/osd.traineddata': 10562727,
    'tessdata/vie.traineddata': 531275,
    'tessdata/chi_sim.traineddata': 2469156,
}
assets = {}
for name, exp in want.items():
    matches = [i for i in zf.infolist() if i.filename.endswith(name)]
    if not matches:
        assets[name] = {'found': False, 'expected': exp}
        continue
    got = matches[0].file_size
    assets[name] = {'found': True, 'expected': exp, 'actual': got, 'ok': got == exp}
r['assets'] = assets

# wheels 数
r['wheels'] = len([i for i in zf.infolist() if i.filename.endswith('.whl')])

# requirements.txt ascii
reqs = [i for i in zf.infolist() if i.filename.endswith('requirements.txt')]
if reqs:
    data = zf.read(reqs[0].filename)
    try:
        data.decode('ascii')
        r['requirements_ascii'] = True
    except Exception as e:
        r['requirements_ascii'] = 'FAIL: %s' % e
else:
    r['requirements_ascii'] = 'MISSING'

# 5 个 .bat：cp936 可解码 + chcp 936 + 无 ❌/⚠
bats = [i for i in zf.infolist() if i.filename.endswith('.bat')]
bat_res = {}
for i in bats:
    data = zf.read(i.filename)
    entry = {}
    try:
        txt = data.decode('cp936')
        entry['cp936'] = True
    except Exception as e:
        entry['cp936'] = 'FAIL: %s' % e
        txt = ''
    entry['chcp936'] = ('chcp 936' in txt)
    entry['no_bad_marks'] = ('\u274c' not in txt and '\u26a0' not in txt)
    entry['name'] = i.filename
    bat_res[i.filename] = entry
r['bats'] = bat_res

# config.default.yaml 与 config.yaml 逐字节
def find(suffix):
    m = [i for i in zf.infolist() if i.filename.endswith(suffix)]
    return m[0].filename if m else None
cdef = find('config.default.yaml')
ccur = [i.filename for i in zf.infolist()
        if i.filename.endswith('/config.yaml') or i.filename == 'config.yaml']
ccur = ccur[0] if ccur else None
r['config_default'] = cdef
r['config_yaml'] = ccur
if cdef and ccur:
    a = zf.read(cdef); b = zf.read(ccur)
    r['config_bytes_equal'] = (a == b)
    r['config_sha256_default'] = hashlib.sha256(a).hexdigest()
    r['config_sha256_yaml'] = hashlib.sha256(b).hexdigest()

# 内容断言
def read_by_suffix(suffix):
    m = [i for i in zf.infolist() if i.filename.endswith(suffix)]
    return zf.read(m[0].filename).decode('utf-8', 'replace') if m else None

checks = {}
mr = read_by_suffix('workflows/payprep/manual_review.py')
checks['manual_review_has_open_encoding'] = bool(mr) and "open(RECON, encoding='utf-8')" in mr
checks['manual_review_has_open_encoding_alt'] = bool(mr) and "open(RECON, encoding='utf-8')" in mr.replace(' ', '').replace('open(RECON,encoding=', "open(RECON, encoding=")

dc = read_by_suffix('workflows/loan_materials/doc_classify.py')
checks['doc_classify_encoding_count'] = dc.count("encoding='utf-8'") if dc else None

jb = read_by_suffix('app/jobs.py')
checks['jobs_has_PYTHONUTF8'] = bool(jb) and 'PYTHONUTF8' in jb

pf = read_by_suffix('tools/preflight.py')
checks['preflight_has_v133'] = bool(pf) and 'v1.3.3-20261016' in pf
r['content_checks'] = checks

print(json.dumps(r, ensure_ascii=False, indent=2, sort_keys=True))
