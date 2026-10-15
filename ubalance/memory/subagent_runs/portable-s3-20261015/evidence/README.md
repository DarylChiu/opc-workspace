# evidence/ — portable-s3-20261015 证据索引

全部为**实测产出**（HTTP 交互、对拍明细、红线扫描）。原始文件未修改。

| 文件 | 内容 |
|---|---|
| `web_drive.py` | **HTTP 驱动脚本**：完全模拟页面的 `fetch('/api/upload')` + `/api/run` + 轮询 `/api/job`；**不用任何命令行 workflow 调用** |
| `api_state.json` | `GET /api/state` 实取（source_root / 端口 / 流程清单 / runs_dir） |
| `api_jobs_history.txt` | `GET /api/jobs` 实取（6 个 job：5 done + 1 failed 留痕） |
| `payment_web_run.log` / `payment_web_run2.log` / `payment_web_run3.log` / `payment_web_run4.log` / `payment_web_run5.log` | Payment 五轮 Web 运行客户端日志（run1 失败=F1 缺陷；run2/3=OCR 引擎问题暴露；run5=修复后 PASS） |
| `payment_diff.txt` / `payment_diff2.txt` / `payment_diff3.txt` | Payment 对拍明细。**`payment_diff3.txt` = 最终 PASS 版（3 文件差异 0）**；前两个保留作缺陷对比 |
| `loan_web_run.log` / `loan_web_run2.log` | Loan 两轮 Web 运行客户端日志 |
| `loan_verify.txt` | Loan 对拍：Outcome1 逐单元格 0 差异 / Outcome2 结构 / 处理报告差异行 / **HTTP 下载的 Outcome2.zip 70 文件 md5 全等** |
| `loan_artifacts_api.txt` | Loan job 产物清单（经 `/api/job` 实取） |
| `loan_outcome2_structure.txt` | 下载的 `Outcome2.zip` 结构复核（20 目录 / 70 文件 / 空目录保留） |
| `loan_download_headers.txt` | 下载响应头（200 + Content-Length + Content-Disposition） |
| `Outcome2_zip_md5.txt` | 下载 zip 的 md5（`79917c848af1673810baf93f7b5eace4`；19 MB 原件未留，只留哈希） |
| `index_served.html` | `GET /` 实取的 HTML（用于外链扫描） |
| `index_external_link_scan.txt` | **零外链扫描**：`http(s)://` 0 / 协议相对 `//` 0 / `script src`·`link href`·`@import`·`url(` 0 |
| `server_startup.log` | 服务启动横幅（绑定 127.0.0.1 + 端口 + 留痕目录） |
| `server_stop.txt` | 停服证据（kill → lsof 空 → ps 无常驻） |
| `start_stop_smoke.txt` | `start.command` / `stop.command` 冒烟（起服务 → GET / 200 → 停止） |
| `redlines.txt` | 红线扫描：`scripts/` md5（前后一致）、md2docx md5、127.0.0.1 监听、无 Mac 硬编码、无 POSIX-only、Toshiba 最新文件、`work/` 今日新增 0 |
| `scripts_md5_before.txt` | S3 开始前的 `scripts/` 汇总 md5（用于前后比对） |

## 复现方式

```bash
cd /Users/zhaoyuzhao/.openclaw/workspace-balance
python3 -u portable/app/server.py --no-browser &      # 起服务（仅 127.0.0.1:8000）
# Payment（经 HTTP）
python3 -u memory/subagent_runs/portable-s3-20261015/evidence/web_drive.py payment \
  work/payprep-20261013/in/10-12华特明细待确认.xlsx \
  work/payprep-20261013/in/voucher-a1013.zip \
  work/payprep-20261013/in/voucher-b1013.zip \
  work/payprep-20261013/in/voucher-c1013.zip --params '{"date":"20261013"}'
# Loan（经 HTTP）
python3 -u memory/subagent_runs/portable-s3-20261015/evidence/web_drive.py loan \
  work/loan-materials-2025-12/in/L1-成品采购入库补单测试20条.xlsx \
  --params '{"override":"config.regression-2025_12.yaml"}'
# 对拍
python3 portable/tools/compare_xlsx.py --base <基线.xlsx> --new <新.xlsx>
kill $(head -n1 portable/runs/.server.pid)
```
