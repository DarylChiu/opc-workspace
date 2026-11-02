#!/usr/bin/env python3
"""
生成 mihomo 生产配置：节点 + 517条分流规则，全部随订阅自愈。

为什么不用 proxy-providers：
    mihomo 内置拉取在这个订阅服务器上会报 `Get ...: EOF`（TLS/指纹层面），
    而 curl 直连同一 URL 返回 200。改用「脚本拉取 + 生成内联配置 + API 热重载」，
    等效于自愈，且不依赖 mihomo 的拉取实现。

用法:
    python3 build_mihomo_config.py              # 生成配置
    python3 build_mihomo_config.py --check      # 生成 + mihomo -t 校验
    python3 build_mihomo_config.py --reload     # 生成 + 热重载运行中的 mihomo
"""
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import urllib.request
from pathlib import Path

HOME = Path.home()
DB = HOME / "Library/Application Support/com.wfnetwork/database.sqlite"
OUT_DIR = HOME / ".openclaw/workspace/memory/network"
OUT_CFG = OUT_DIR / "mihomo_prod.yaml"
OUT_SECRET = OUT_DIR / ".mihomo_secret"
GEO_SRC = HOME / "Library/Application Support/com.wfnetwork"

MIXED_PORT = int(os.environ.get("MIHOMO_PORT", "7893"))
BIND = os.environ.get("MIHOMO_BIND", "127.0.0.1")
EXT_CTRL = os.environ.get("MIHOMO_CTRL", "127.0.0.1:19093")
UA = "clash-verge/v2.0.0"
EXCLUDE = "香港 02"  # short-id 非法，mihomo 会 fatal
GROUP_MAP = {"微风网络": "PROXY", "自动选择": "AUTO", "故障转移": "FALLBACK"}


def get_sub_url() -> str:
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    row = con.execute("SELECT url FROM profiles LIMIT 1").fetchone()
    con.close()
    if not row or not row[0]:
        sys.exit("✗ 无法从 database.sqlite 读到订阅 URL")
    return row[0].strip()


def fetch_sub(url: str) -> dict:
    """用 curl 拉订阅（mihomo 内置拉取会 EOF，curl 正常）。"""
    r = subprocess.run(
        ["curl", "-sS", "--max-time", "30", "--noproxy", "*", "-A", UA, url],
        capture_output=True, text=True,
    )
    if r.returncode != 0 or not r.stdout:
        sys.exit(f"✗ 订阅拉取失败 (exit={r.returncode}): {r.stderr.strip()[:200]}")
    import yaml
    d = yaml.safe_load(r.stdout)
    if not isinstance(d, dict) or "proxies" not in d:
        sys.exit(f"✗ 订阅返回格式异常（顶层类型 {type(d).__name__}）")
    return d


def build(sub: dict, sub_url: str) -> str:
    proxies = sub.get("proxies", [])
    rules = sub.get("rules", [])
    if not proxies or not rules:
        sys.exit(f"✗ 订阅数据不完整: proxies={len(proxies)}, rules={len(rules)}")

    # 1) 剔除坏节点
    kept = [p for p in proxies if EXCLUDE not in p.get("name", "")]
    dropped = len(proxies) - len(kept)

    # 2) 组名重映射（订阅引用「微风网络」，本站组名 PROXY，不换会加载失败）
    def remap(s: str) -> str:
        for old, new in GROUP_MAP.items():
            s = re.sub(rf"(?<![A-Za-z0-9_-]){re.escape(old)}(?![A-Za-z0-9_.-])", new, s)
        return s
    rules = [remap(str(r)) for r in rules]

    # TikTok / 字节海外系强制走 NON-HK：香港节点被 TikTok 封（实测返回 302，SG/JP/US 均 200）
    tiktok_rules = [
        "DOMAIN-SUFFIX,tiktok.com,NON-HK",
        "DOMAIN-SUFFIX,tiktokv.com,NON-HK",
        "DOMAIN-SUFFIX,tiktokcdn.com,NON-HK",
        "DOMAIN-SUFFIX,byteoversea.com,NON-HK",
        "DOMAIN-SUFFIX,ibyteimg.com,NON-HK",
        "DOMAIN-SUFFIX,muscdn.com,NON-HK",
        "DOMAIN-KEYWORD,tiktok,NON-HK",
    ]
    # 插在第一条 MATCH 之前（即所有规则尾部之前），确保优先于 GEOIP,CN 但又不破坏原有顺序
    rules = tiktok_rules + rules

    # 3) DNS：修复冷启动自举循环
    dns = dict(sub.get("dns") or {})
    dns.update({
        "enable": True,
        "ipv6": False,
        # 原订阅把 DoH/TLS 排在前面，冷启动时全超时 → 永远轮不到可用 UDP
        "nameserver": ["223.5.5.5", "119.29.29.29", "114.114.114.114"],
        "default-nameserver": ["223.5.5.5", "119.29.29.29", "114.114.114.114"],
        "proxy-server-nameserver": ["43.108.56.44"],  # 节点域名仅此私有DNS可解析，公共DNS全部失败
        # respect-rules=true 会让订阅域名被规则判进 PROXY，但代理还没起来 → 死锁
        "respect-rules": False,
        "fallback": ["https://1.1.1.1/dns-query", "tls://8.8.8.8"],
        "fallback-filter": {"geoip": True, "geoip-code": "CN", "ipcidr": ["240.0.0.0/4"],
                            "domain": ["+.google.com", "+.facebook.com", "+.youtube.com"]},
        # 订阅域名必须解析成真实 IP，不能被 fake-ip 劫持
        "fake-ip-filter": list(dns.get("fake-ip-filter") or []) + [
            "*.weifengapi.com", "*.weifengchat.vip", "*.lan", "*.local",
        ],
    })

    # TikTok 分流组：香港被 TikTok 封（返回 302），必须排除所有香港节点
    non_hk = [p["name"] for p in kept if "香港" not in p["name"] and "HK" not in p["name"].upper()]

    groups = [
        {"name": "PROXY", "type": "select", "proxies": ["AUTO", "NON-HK", "FALLBACK"] + [p["name"] for p in kept]},
        {"name": "NON-HK", "type": "url-test", "proxies": non_hk or ["AUTO"],
         "url": "http://www.gstatic.com/generate_204", "interval": 300, "tolerance": 50},
        {"name": "AUTO", "type": "url-test", "proxies": [p["name"] for p in kept],
         "url": "http://www.gstatic.com/generate_204", "interval": 300, "tolerance": 50},
        {"name": "FALLBACK", "type": "fallback", "proxies": [p["name"] for p in kept],
         "url": "http://www.gstatic.com/generate_204", "interval": 300},
    ]

    secret = OUT_SECRET.read_text().strip() if OUT_SECRET.exists() else ""
    if not secret:
        secret = secrets.token_urlsafe(24)
        OUT_SECRET.write_text(secret)
        OUT_SECRET.chmod(0o600)

    cfg = {
        "mixed-port": MIXED_PORT,
        "allow-lan": os.environ.get("MIHOMO_LAN","0") == "1",
        "mode": "rule",
        "log-level": "warning",
        "ipv6": False,
        "unified-delay": True,
        "tcp-concurrent": True,
        "bind-address": BIND,
        "external-controller": EXT_CTRL,
        "secret": secret,
        "geodata-mode": True,
        "geodata-loader": "memconservative",
        "profile": {"store-selected": True, "store-fake-ip": True},
        "dns": dns,
        "proxies": kept,
        "proxy-groups": groups,
        "rules": rules,
    }

    import yaml
    header = (
        "# mihomo 生产配置 · 由 build_mihomo_config.py 自动生成，请勿手工编辑\n"
        f"# 源: {sub_url.split('token=')[0]}token=***\n"
        f"# 节点 {len(kept)} 个（剔除 {dropped} 个坏节点: {EXCLUDE}）· 规则 {len(rules)} 条\n"
        "# 刷新: python3 build_mihomo_config.py --reload  （建议 cron 每日）\n"
    )
    return header + yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False, width=4096)


def ensure_geo() -> list[str]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    missing = []
    for name in ("GEOIP.dat", "GEOSITE.dat", "GEOIP.metadb", "ASN.mmdb"):
        src, dst = GEO_SRC / name, OUT_DIR / name
        if src.exists():
            if not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime:
                dst.write_bytes(src.read_bytes())
        elif not dst.exists():
            missing.append(name)
    return missing


def main() -> int:
    print("→ 读取订阅 URL ...")
    sub_url = get_sub_url()
    print("→ 拉取订阅 ...")
    sub = fetch_sub(sub_url)
    n_px, n_rule = len(sub.get("proxies", [])), len(sub.get("rules", []))
    print(f"  原始: {n_px} 节点 / {n_rule} 规则")

    print("→ 生成配置 ...")
    cfg = build(sub, sub_url)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_CFG.write_text(cfg)
    OUT_CFG.chmod(0o600)

    missing = ensure_geo()
    if missing:
        print(f"⚠️  缺少 GEO: {missing}（mihomo 会去 GitHub 下载，直连会卡死）", file=sys.stderr)

    n_kept = len(sub["proxies"]) - sum(1 for p in sub["proxies"] if EXCLUDE in p.get("name", ""))
    print(f"✓ 已生成 {OUT_CFG}")
    print(f"  节点 {n_kept} 个 · 规则 {len(sub['rules'])} 条 · 端口 {MIXED_PORT} · 控制 {EXT_CTRL}")

    if "--check" in sys.argv or "--reload" in sys.argv:
        print("→ mihomo -t 校验 ...")
        r = subprocess.run(["mihomo", "-d", str(OUT_DIR), "-f", str(OUT_CFG), "-t"],
                           capture_output=True, text=True)
        ok = r.returncode == 0
        print((r.stdout + r.stderr).strip().splitlines()[-1])
        if not ok:
            return 1

    if "--reload" in sys.argv:
        secret = OUT_SECRET.read_text().strip()
        print("→ 热重载运行中的 mihomo ...")
        r = subprocess.run(
            ["curl", "-sS", "-X", "PUT", "--max-time", "10",
             "-H", f"Authorization: Bearer {secret}",
             f"http://{EXT_CTRL}/configs?force=true",
             "-d", json.dumps({"path": str(OUT_CFG)})],
            capture_output=True, text=True,
        )
        print(f"  {'✓ 重载成功' if r.returncode == 0 else '⚠️  重载失败（可能未运行）: ' + r.stderr.strip()[:120]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
