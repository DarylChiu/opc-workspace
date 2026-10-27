# Daryl — 个人信息与设备

## 设备清单
| 设备 | 系统 | 用途 |
|------|------|------|
| iPhone | iOS | 飞书客户端 |
| Samsung Tab S8 | Android (One UI) | 平板 |
| Mac | macOS | 桌面端/开发机 |

## 出差规则
- **Daryl 说出差 = 只带 Samsung Tab S8 + iPhone**
- **不带 Mac** 出门

## 语音交互状态 (2026-07-17)
| 设备 | 语音输入 | 备注 |
|------|----------|------|
| iPhone | ❌ 有问题 | 雅思陪练App语音输入故障 |
| Samsung Tab S8 | ✅ 可用 | 交互有拖沓感 |
| Mac | — | 桌面端 |

## 版本状态
- 雅思陪练助手 v1.1.0 已挂起，待 Daryl 发起 Debug 迭代

## 成本与图像识别政策 (2026-08-27 指令)
- **图像识别 = 本地 OCR 优先**（tesseract: /opt/homebrew/bin/tesseract），**禁止**用 openrouter / deepseek 的图像识别
- 任何服务直连 LLM API 必须独立 key，禁止继承 OpenClaw 主 key
- 停用必须验证（disable 后重读配置确认 0 残留）
- 关停服务必须查 launchd 复活链（KeepAlive/守护脚本）
- 成本账本只认 DeepSeek 平台侧真实消耗，OpenClaw 侧账本仅参考

---
> 来源: xiaofeng (Bryson) 2026-07-17 设备配置同步
> ✅ 已确认 & 更新 (Kitty 2026-07-14) — 三设备清单无误,出差=TabS8+iPhone规则已纳入决策
