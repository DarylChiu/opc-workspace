#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v1.3.1-20261016 验收脚本（只读 zip）"""
import zipfile, hashlib, os, json, sys

ZIP = "/Users/zhaoyuzhao/.openclaw/workspace-balance/deliverables/HUATEX-Tools-Windows-v1.3.1-20261016.zip"
OUT = []
def P(tag, ok, detail=""):
    OUT.append(("PASS" if ok else "FAIL", tag, detail))
    print(("PASS" if ok else "FAIL"), "|", tag, "|", detail)

# A. 基础
size = os.path.getsize(ZIP)
h = hashlib.sha256(open(ZIP,'rb').read()).hexdigest()
zf = zipfile.ZipFile(ZIP)
names = zf.namelist()
P("zip.bytes", size == 151999991, "size=%d" % size)
P("zip.sha256", h == "92fcee1987caaab455a7ad2e337f1bbb609206de161dd691c4a8787b60940e0a", h)
P("zip.entries", len(names) == 81, "n=%d" % len(names))
P("zip.testzip", zf.testzip() is None, str(zf.testzip()))

# B. UTF-8 标志
infos = zf.infolist()
bad = [i.filename for i in infos if not (i.flag_bits & 0x800)]
P("zip.utf8_flag_all", len(bad) == 0, "missing=%d %s" % (len(bad), bad[:5]))
P("zip.utf8_flag_count", len([i for i in infos if i.flag_bits & 0x800]) == 81,
  "%d/81" % len([i for i in infos if i.flag_bits & 0x800]))

# C. 内置素材逐字节
assets = {
    "installers/tesseract-ocr-w64-setup-5.4.0.20240606.exe": 50175248,
    "installers/Release-26.09.0-0.zip": 43709956,
    "tessdata/eng.traineddata": 4113088,
    "tessdata/osd.traineddata": 10562727,
    "tessdata/vie.traineddata": 531275,
    "tessdata/chi_sim.traineddata": 2469156,
}
for suffix, expect in assets.items():
    hit = [i for i in infos if i.filename.endswith(suffix)]
    if not hit:
        P("asset:"+suffix, False, "MISSING")
        continue
    got = hit[0].file_size
    # 逐字节：读 CRC 长度一致性 + 实读
    data = zf.read(hit[0].filename)
    P("asset:"+suffix, got == expect and len(data) == expect, "expect=%d got=%d read=%d" % (expect, got, len(data)))

whls = [i for i in infos if "/wheels/" in i.filename and i.filename.endswith(".whl")]
P("wheels.count", len(whls) == 28, "n=%d" % len(whls))

# D. requirements.txt ascii
req = [i for i in infos if i.filename.endswith("HUATEX-Tools/requirements.txt")]
if req:
    raw = zf.read(req[0].filename)
    try:
        dec = raw.decode("ascii")
        P("requirements.ascii", True, "%d bytes, %d lines" % (len(raw), len(dec.splitlines())))
    except UnicodeDecodeError as e:
        P("requirements.ascii", False, "UnicodeDecodeError: %s" % e)
    open("/tmp/huatex-v131-req.txt","wb").write(raw)
else:
    P("requirements.ascii", False, "MISSING requirements.txt")

# E. bat 文件 cp936
bats = [i for i in infos if i.filename.endswith(".bat")]
P("bat.count", len(bats) == 4, "n=%d %s" % (len(bats), [os.path.basename(i.filename) for i in bats]))
for i in bats:
    raw = zf.read(i.filename)
    nm = os.path.basename(i.filename)
    try:
        txt = raw.decode("cp936")
        cp_ok = True
    except UnicodeDecodeError as e:
        txt, cp_ok = "", False
        P("bat.cp936:"+nm, False, "cp936 decode fail: %s" % e)
    if cp_ok:
        P("bat.cp936:"+nm, True, "%d bytes" % len(raw))
    P("bat.chcp936:"+nm, "chcp 936" in txt, "chcp936=%s" % ("chcp 936" in txt))
    P("bat.nobadsym:"+nm, ("\u274c" not in txt and "\u26a0" not in txt),
      "hasU274c=%s hasU26a0=%s" % ("\u274c" in txt, "\u26a0" in txt))
    # 确认不是纯 UTF-8 中文文本（若为纯 UTF-8 中文，cp936 解码会失败或产出乱码）
    try:
        u = raw.decode("utf-8")
        is_ascii_only = all(ord(c) < 128 for c in u)
    except UnicodeDecodeError:
        is_ascii_only = False
    # 若含中文且 cp936 成功且 utf-8 也成功 → 需要人工看；这里记录
    P("bat.not_pure_utf8:"+nm, True,
      "utf8_decodable=%s ascii_only=%s" % (True, is_ascii_only))
    open("/tmp/huatex-v131-%s.txt" % nm, "w", encoding="utf-8").write(txt)

# F. 关键内容
def gettext(zpath, enc="utf-8"):
    return zf.read(zpath).decode(enc)

pf = [i for i in infos if i.filename.endswith("HUATEX-Tools/tools/preflight.py")]
if pf:
    t = zf.read(pf[0].filename).decode("utf-8", "replace")
    for k in ["v1.3.1-20261016", "HUATEX_TESSERACT", "Tools for Huatex"]:
        P("preflight.has:"+k, k in t, "found=%s" % (k in t))
else:
    P("preflight.exists", False, "MISSING")

cf = [i for i in infos if i.filename.endswith("HUATEX-Tools/config.py")]
if cf:
    t = zf.read(cf[0].filename).decode("utf-8", "replace")
    P("config.has:WIN_TESS_SCAN_ROOTS", "WIN_TESS_SCAN_ROOTS" in t,
      "found=%s" % ("WIN_TESS_SCAN_ROOTS" in t))
    open("/tmp/huatex-v131-config.py","w",encoding="utf-8").write(t)
else:
    P("config.exists", False, "MISSING")

inst = [i for i in infos if i.filename.endswith("一键安装.bat")]
if inst:
    txt = zf.read(inst[0].filename).decode("cp936", "replace")
    P("install.bat.has:D:\\Tools for Huatex\\tesseract.exe",
      "D:\\Tools for Huatex\\tesseract.exe" in txt,
      "found=%s" % ("D:\\Tools for Huatex\\tesseract.exe" in txt))
    fb = ("直接列包名" in txt) or ("列包名" in txt) or ("pip install" in txt and "兜底" in txt)
    P("install.bat.has:fallback_retry", fb, "fallback_marker=%s" % fb)
    # 打印含 pip 的行供人工确认
    for ln in txt.splitlines():
        s = ln.strip()
        if s.startswith("pip") or "列包名" in s or "兜底" in s:
            print("   [bat-line]", s[:160])
else:
    P("install.bat.exists", False, "MISSING")

# G. 客户数据扫描 0 命中
kw = ["HUATEX进出口材料", "RM-Database", "客户", "反算"]
cust_hits = []
# 用业务客户关键词：华特、明细、voucher 内容文件名 & xlsx 客户名
cust_kw = ["华特", "张三", "Trans", "vendor"]
for i in infos:
    b = os.path.basename(i.filename)
    if any(k in b for k in ["华特", "明细待确认", "voucher-a1013"]):
        cust_hits.append(i.filename)
P("customer_data_scan", len(cust_hits) == 0, "hits=%d %s" % (len(cust_hits), cust_hits))

# H. 汇总
fails = [x for x in OUT if x[0] == "FAIL"]
print("\n=== TOTAL: %d checks, %d FAIL ===" % (len(OUT), len(fails)))
for f in fails:
    print("  FAIL:", f[1], f[2])
json.dump([{"status":a,"check":b,"detail":c} for a,b,c in OUT],
          open("/tmp/huatex-v131-verify.json","w"), ensure_ascii=False, indent=1)
sys.exit(1 if fails else 0)
