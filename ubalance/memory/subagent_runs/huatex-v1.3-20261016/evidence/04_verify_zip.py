#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v1.3-20261016 交付包验收：字节数/sha256/条目数、testzip、UTF-8 标志、内置素材逐字节、包内标识。"""
import hashlib, io, os, sys, zipfile

ZIP = sys.argv[1]
EXPECT_ASSETS = {
    'HUATEX-Tools/installers/tesseract-ocr-w64-setup-5.4.0.20240606.exe': 50175248,
    'HUATEX-Tools/installers/Release-26.09.0-0.zip': 43709956,
    'HUATEX-Tools/tessdata/eng.traineddata': 4113088,
    'HUATEX-Tools/tessdata/osd.traineddata': 10562727,
    'HUATEX-Tools/tessdata/vie.traineddata': 531275,
    'HUATEX-Tools/tessdata/chi_sim.traineddata': 2469156,
}

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()

fails = []
print('== 验收：%s ==' % ZIP)
size = os.path.getsize(ZIP)
sha = sha256_file(ZIP)
zf = zipfile.ZipFile(ZIP)
infos = zf.infolist()
n = len(infos)
print('[1] 字节数     : %d' % size)
print('[1] sha256     : %s' % sha)
print('[1] 条目数     : %d' % n)

bad = zf.testzip()
print('[2] testzip()  : %s' % ('None (OK)' if bad is None else 'FAIL: %s' % bad))
if bad is not None:
    fails.append('testzip 报损坏：%s' % bad)

noflag = [i.filename for i in infos if not (i.flag_bits & 0x800)]
print('[3] UTF-8 0x800: %d/%d 带标志，缺 %d 条' % (n - len(noflag), n, len(noflag)))
if noflag:
    fails.append('缺 UTF-8 标志：%s' % noflag[:5])

print('[4] 内置素材逐字节核对：')
names = set(zf.namelist())
for rel, exp in sorted(EXPECT_ASSETS.items()):
    if rel not in names:
        print('    MISSING %s' % rel); fails.append('缺文件 %s' % rel); continue
    got = zf.getinfo(rel).file_size
    ok = (got == exp)
    print('    %s  %d B  %s' % ('OK ' if ok else 'FAIL', got, rel))
    if not ok:
        fails.append('%s 字节 %d != %d' % (rel, got, exp))
whls = [x for x in names if x.startswith('HUATEX-Tools/wheels/') and x.endswith('.whl')]
print('    wheels 数量 : %d  %s' % (len(whls), 'OK' if len(whls) == 28 else 'FAIL'))
if len(whls) != 28:
    fails.append('wheels 数 %d != 28' % len(whls))

def grep_in_zip(rel, needles):
    data = zf.read(rel)
    try:
        txt = data.decode('utf-8')
    except UnicodeDecodeError:
        txt = data.decode('utf-8', 'replace')
    miss = [s for s in needles if s not in txt]
    return miss

print('[5] 包内文件内容标识：')
checks = [
    ('HUATEX-Tools/tools/preflight.py', ['v1.3-20261016', 'HUATEX_TESSERACT', 'Tools for Huatex', 'cd /d']),
    ('HUATEX-Tools/config.py', ['WIN_TESS_SCAN_ROOTS', 'scan_tesseract']),
    ('HUATEX-Tools/一键安装.bat', ['D:\\Tools for Huatex\\tesseract.exe']),
]
for rel, needles in checks:
    if rel not in names:
        print('    MISSING %s' % rel); fails.append('缺文件 %s' % rel); continue
    miss = grep_in_zip(rel, needles)
    print('    %s  %s  %s' % ('OK ' if not miss else 'FAIL', rel, '' if not miss else '缺：%s' % miss))
    if miss:
        fails.append('%s 缺标识 %s' % (rel, miss))

print()
if fails:
    print('结论：FAIL ❌  共 %d 项' % len(fails))
    for f in fails:
        print('  - %s' % f)
    sys.exit(1)
print('结论：全部 PASS ✅')
print('ZIP_BYTES=%d' % size)
print('ZIP_SHA256=%s' % sha)
print('ZIP_ENTRIES=%d' % n)
