#!/usr/bin/env bash
# regress_invoices.sh — 越南发票解析回归（C8）
# 样本 = tests/fixtures/invoices/*.pdf（从真实凭证包只读复制，不修改原包）
# 断言 = 发票号（含前导 0）/ 日期 / 金额 / 税号 / 序列号 / 调整票标记
# 任一条失败 → 非 0 退出并打印差异
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE/.." || exit 1
exec python3 -u scripts/regress_invoices.py "$@"
