#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v1.3.4-20261016 交付包验收（只读）"""
import zipfile, hashlib, os, sys, json

ZIP = sys.argv[1]
EXPECT = {
    'installers/tesseract-ocr-w64-setup-5.4.0.20240606.exe': 50175248,
    'installers/Release-26.09.0-0.zip': 43709956,
    'tessdata/eng.traineddata': 4113088,
    'tessdata/osd.traineddata': 10562727,
    'tessdata/vie.traineddata': 531275,
    'tessdata/chi_sim.traineddata': 2469156,
}
res = {}
data = open(ZIP, 'rb').read()
res['size'] = len(data)
res['sha256'] = hashlib.sha256(data).hexdigest()
z = zipfile.ZipFile(ZIP)
names = z.namelist()
res['entries'] = len(names)
res['testzip'] = z.testzip()            # must be None
res['wheels'] = sum(1 for n in names if n.endswith('.whl'))

# UTF-8 flag (0x800) on every entry
bad_flag = [n for n in names if not (z.getinfo(n).flag_bits & 0x800)]
res['utf8_missing'] = bad_flag

# 6 assets byte-exact
asset_ok = {}
for n, sz in EXPECT.items():
    real = [x for x in names if x.endswith(n)]
    if not real:
        asset_ok[n] = 'MISSING'
        continue
    info = z.getinfo(real[0])
    asset_ok[n] = 'OK' if info.file_size == sz else 'SIZE %d != %d' % (info.file_size, sz)
res['assets'] = asset_ok

# requirements.txt ascii
req = [n for n in names if n.endswith('requirements.txt')]
if req:
    raw = z.read(req[0])
    try:
        raw.decode('ascii')
        res['requirements_ascii'] = 'OK'
    except UnicodeDecodeError:
        res['requirements_ascii'] = 'NON-ASCII'
else:
    res['requirements_ascii'] = 'MISSING'

# 5 .bat files: cp936 decodable, contain 'chcp 936', no ❌/⚠
bats = [n for n in names if n.endswith('.bat')]
bat_res = {}
for b in bats:
    raw = z.read(b)
    try:
        txt = raw.decode('gbk')
        d = 'cp936-OK'
    except UnicodeDecodeError as e:
        d = 'cp936-FAIL(%s)' % e
    bat_res[b] = {'decode': d, 'chcp936': ('chcp 936' in (raw.decode('gbk', 'replace'))),
                  'has_emoji': any(ch in raw.decode('gbk', 'replace') for ch in ('❌', '⚠'))}
res['bats'] = bat_res
res['bat_count'] = len(bats)

# config.default.yaml == config.yaml
def find(sfx):
    return [n for n in names if n.endswith(sfx)]
cd = find('config.default.yaml'); cy = [n for n in names if n.endswith('/config.yaml')]
if cd and cy:
    res['config_match'] = (z.read(cd[0]) == z.read(cy[0]))
else:
    res['config_match'] = 'MISSING %s %s' % (cd, cy)

# content markers
def has(sfx, needles):
    cands = [n for n in names if n.endswith(sfx)]
    if not cands:
        return 'MISSING'
    txt = z.read(cands[0]).decode('utf-8', 'replace')
    return {k: (v in txt) for k, v in needles.items()}
res['server_py'] = has('app/server.py', {'single_quote_write': "'{safe}'", 'v134_comment': '1.3.4'})
res['config_py'] = has('config.py', {'load_yaml_tolerant': 'load_yaml_tolerant', 'repair_yaml_quotes': 'repair_yaml_quotes'})
res['jobs_py'] = has('app/jobs.py', {'load_yaml_tolerant': 'load_yaml_tolerant'})
res['preflight_py'] = has('tools/preflight.py', {'version': 'v1.3.4-20261016'})

# customer-data scan: look for known customer markers in text-ish entries
CUST = ['RM-Database', 'HUATEX进出口材料', '客户数据']
hits = []
for n in names:
    if n.endswith(('.py', '.txt', '.md', '.bat', '.yaml', '.html', '.csv')):
        try:
            t = z.read(n).decode('utf-8', 'replace')
        except Exception:
            continue
        for c in CUST:
            if c in t:
                hits.append('%s:%s' % (n, c))
res['customer_hits'] = hits

print(json.dumps(res, ensure_ascii=False, indent=1))
