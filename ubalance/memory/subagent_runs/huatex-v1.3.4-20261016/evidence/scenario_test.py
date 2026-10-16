#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v1.3.4 本场景实测：页面⓪写坏 config.yaml 的自愈 + 写回单引号
用法: python3 scenario_test.py <包根目录>
"""
import io, os, re, sys, glob, importlib.util, shutil
import yaml

ROOT = sys.argv[1]
os.chdir(ROOT)
sys.path.insert(0, ROOT)

print("== 包根:", ROOT)
print("== config.yaml line 27 初始:", repr(io.open('config.yaml', encoding='utf-8').read().splitlines()[26]))

# ---------- 复现：把 source_root 写成双引号 Windows 路径（真机页面⓪的写法） ----------
t = io.open('config.yaml', encoding='utf-8').read()
new, n = re.subn(r'(?m)^(\s*source_root:\s*).*$',
                 r'\1"D:\\Tools for Huatex\\HUATEX进出口材料"', t)
assert n == 1
io.open('config.yaml', 'w', encoding='utf-8').write(new)
print("\n[1] 写入双引号路径后 line 27:", repr([l for l in new.splitlines() if l.strip().startswith('source_root:') and 'hint' not in l][0]))
try:
    yaml.safe_load(new)
    print("    ❌ 裸 yaml.safe_load 未报错（预期 ScannerError）")
except Exception as e:
    print("    ✅ 裸 yaml.safe_load →", type(e).__name__, "|", str(e).replace('\n', ' | '))

# ---------- 包内 config.load_yaml_tolerant 自愈 ----------
print("\n[2] 包内 config.load_yaml_tolerant('config.yaml')")
import config as cfg
d = cfg.load_yaml_tolerant('config.yaml')
line = [l for l in io.open('config.yaml', encoding='utf-8').read().splitlines()
        if l.strip().startswith('source_root:') and 'hint' not in l][0]
print("    ✅ 解析成功 source_root =", repr(d['paths']['source_root']))
print("    ✅ 写回行 =", repr(line), "→ 单引号:", line.strip().startswith("source_root: '"))
baks = sorted(glob.glob('config.yaml*'))
print("    ✅ 目录文件:", baks)
bk = 'config.yaml.bak'
if os.path.exists(bk):
    bl = [l for l in io.open(bk, encoding='utf-8').read().splitlines()
          if l.strip().startswith('source_root:') and 'hint' not in l][0]
    print("    ✅ .bak 保留原双引号行 =", repr(bl))
print("    ✅ 修复后裸 yaml 可解析 =",
      repr(yaml.safe_load(io.open('config.yaml', encoding='utf-8').read())['paths']['source_root']))

# ---------- 包内 app/server.py::save_source_root（含反斜杠的真实目录） ----------
print("\n[3] 包内 app/server.py::save_source_root（目录名含反斜杠）")
spec = importlib.util.spec_from_file_location('srv', os.path.join(ROOT, 'app/server.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
target = os.path.join(os.path.dirname(ROOT.rstrip('/')), 'D:\\Tools for Huatex\\HUATEX进出口材料')
os.makedirs(target, exist_ok=True)
print("    target =", repr(target), "| 存在:", os.path.isdir(target), "| 含反斜杠:", '\\' in target)
ok, msg = m.save_source_root(target)
raw = io.open('config.yaml', encoding='utf-8').read()
line = [l for l in raw.splitlines() if l.strip().startswith('source_root:') and 'hint' not in l][0]
print("    ✅ save_source_root ->", ok, msg)
print("    ✅ 写回行 =", repr(line))
print("    ✅ 是单引号:", line.strip().startswith("source_root: '"))
print("    ✅ 裸 yaml 解析 =", repr(yaml.safe_load(raw)['paths']['source_root']))
print("    ✅ 往返一致:", yaml.safe_load(raw)['paths']['source_root'] == target)
ok2, _ = m.save_source_root(target)
print("    ✅ 幂等二次:", ok2)
