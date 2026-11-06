# 监控脚本陷阱记录

## 2026-11-06 · 盲扫 sk- 前缀导致误判"API Key 失效"

### 现象
alive_check.sh 报 `DeepSeek 鉴权失败（HTTP 401）—— key 可能失效/欠费`，
但 Daryl 质疑"一定不会是欠费，还有几百块"，实测余额 ¥113.25 充足。

### 根因
脚本用 `v.startswith('sk-')` 盲扫 openclaw.json，**返回第一个匹配项**：
```
plugins.entries.moonshot.config.webSearch.apiKey  ← Kimi/Moonshot 的联网搜索 key
```
拿 Moonshot 的 key 请求 `api.deepseek.com/user/balance` → 必然 401。
错误信息被自己的 `case` 语句包装成"key 失效/欠费"，掩盖了真实原因。

### 教训
1. **凭证查找必须按 provider 精确限定**，禁止按前缀盲扫
2. **401 不能等同于"key 失效或欠费"** —— 也可能是"用错了 key"。
   错误信息必须保留原始 response body（含 request_id），便于追溯
3. **不要在告警文案里替用户下原因结论**（"key 可能失效/欠费"），
   只报事实（HTTP 401 + 原始错误），让判断留给数据
4. **用户质疑告警时，先复现再解释**，不要复述脚本的判断

### 正确做法
1. 优先 `models.providers.<provider>.apiKey` 精确路径
2. 次选按 dict key 名匹配 provider（deepseek/deepseek-native/...）
3. 兜底 `launchctl getenv DEEPSEEK_API_KEY`
4. 报错时附 `request_id` 和原始 message

### 通用原则
监控系统的误报比不报更危险 —— 它会训练用户忽略告警。
