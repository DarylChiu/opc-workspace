# Feishu 通道工具（feishu_doc 等）被 tools.profile 拦截的诊断（2026-10-07）

> 背景：Self 请求为 self 账号放开 `feishu_doc`（建/读写云文档+表格）。诊断结论如下，供 Daryl 确认后执行。

## 结论
- **卡点 = 全局 `tools.profile: "coding"`**（openclaw.json 顶层 `tools.profile`），**不是** `channels.feishu.tools`，也**不是** `agents.self.tools`。
- `coding` 基础白名单只含：group:fs / group:runtime / group:web / group:sessions / group:memory / cron / image / image_generate / music_generate / video_generate。**不含插件/通道工具**（feishu_doc 是 feishu 插件通道工具，非内置，非 bundle-mcp）。

## 证据链
1. `channels.feishu.tools = {}` → `resolveToolsConfig` 默认 `doc:true` → 工具**其实已注册**（`registerFeishuDriveTools` 在 `toolsCfg.doc` 为真时注册 `feishu_doc`）。
2. `accounts.self` 无 tools 段 → 同样走默认（doc:true）。
3. 唯一过滤层 = `tools.profile`。`coding` 不含 feishu_doc → 对 self（及所有 Agent，因为四家都继承全局 profile）不暴露。

## 修复方案（等 Daryl 点头再动，P1）
给 self 单独放开（最小范围，推荐）：
```json
// agents.list 的 self 条目加 tools 字段
{ "id": "self", "model": "deepseek/deepseek-v4-flash",
  "workspace": "/Users/zhaoyuzhao/.openclaw/workspace-self",
  "tools": { "alsoAllow": ["feishu_doc"] } }
```
- 全局版 `tools.alsoAllow: ["feishu_doc"]` 会让四家都能用，不推荐。
- 工具名精确为 `feishu_doc`（还有 `feishu_wiki`/`feishu_perm`/`feishu_app_scopes`/`feishu_bitable_*`/`feishu_chat`/`feishu_drive` 等）。

## 注意
- 若 Daryl 的「推进面板」是**多维表格（bitable）**而非文档内表格，对应工具是 `feishu_bitable_*`（如 `feishu_bitable_create_record`），不是 `feishu_doc`。文档内表格用 `feishu_doc` 的 `insert_table_row`/`write_table_cells`。
- 放开后若报权限不足，需飞书开放平台侧授权 `docx:document` + `docx:document.block:convert` + `drive:drive` 并发布版本（Self 已表态这块请 Daryl 处理）。
