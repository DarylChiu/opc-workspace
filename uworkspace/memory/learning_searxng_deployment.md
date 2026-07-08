# Learning: SearXNG部署和使用

## 来源: 2026-03-24 ~ 2026-03-30

### 背景
- 为替换Kimi Websearch API部署SearXNG
- 部署完成于2026-03-28，服务运行在端口8888 (PID 19662)

### 技术细节
- SearXNG作为本地搜索聚合服务
- 通过adapter适配OpenClaw的web_search接口
- 定期生成使用报告：`python3 ~/.openclaw/workspace/searxng-adapter/generate_searxng_report.py`

### 状态
- ✅ 已部署并运行
- 需定期检查服务健康状态
