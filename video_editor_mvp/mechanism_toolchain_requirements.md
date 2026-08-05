# 决策账本 + 回滚工具链 · 需求清单

> 日期: 2026-08-05 | 用途: Kitty 提议 Daryl 同意后即可开搭（机制分层：细节级自主决策的留痕与可逆）
> 配套原则: 「只加机制，不加细节限制」——工具链只保证可追溯+可回滚，不干预决策内容

---

## 一、决策账本（Decision Ledger）

**目标**: 每个细节级自主决策留痕，事后可审计、可回滚、可蒸馏进用户替身

### 数据模型（JSONL，每行一条决策）
```json
{
  "id": "dec_20260805_001",
  "ts": "2026-08-05T13:00:00+07:00",
  "project": "video_editor_mvp",
  "module": "scan",
  "level": "detail",                 // direction | detail
  "decision": "素材卡片默认显示别名而非原始文件名",
  "rationale": "用户替身推演: 原始名 VID_..._151812_00_185 无法对号入座",
  "alternatives": ["显示完整时间", "显示拍摄时间+序号"],
  "evidence": ["session:f72e369f#L123", "feedback:20260731"],   // 证据来源
  "confidence": 0.85,
  "status": "active",                // active | rolled_back
  "rollback_ref": "git:abc1234"      // 回滚点引用（见二）
}
```

### 写入时机（强制）
- 细节级决策发生时自动 append（代码实现层：工具函数 `ledger.record(...)`）
- 方向级决策也记录（Daryl 确认后落一条，含确认人/渠道）——「确认记录制度化」落地
- 用户纠正/反馈 → 立即记一条 `type=correction`，作为替身蒸馏输入

### 查询能力
- 按 项目/模块/状态/日期 过滤
- `ledger show <id>` 看单条完整上下文
- `ledger audit <project>` 输出审计报告（哪些决策活跃/回滚/被纠正）

---

## 二、回滚工具链（Rollback Toolchain）

**目标**: 任何决策可一键回到备选方案，成本趋近于零 → 「确认后置」才敢成立

### 回滚点生成（自动）
- 每次细节级实现变更前，自动打回滚点：
  - 代码 → git commit/branch（`git commit` 前置，或 stash 快照）
  - 数据/DB → 变更前快照（文件拷贝或 sqlite backup）
  - 前端 → 与代码同源，git 覆盖
- 回滚点引用写回账本条目（rollback_ref）

### 回滚操作
- `rollback dec_20260805_001` → 找到 rollback_ref → git checkout / 快照恢复 → 账本状态改 `rolled_back` → 若选择备选方案则新开一条决策记录
- 回滚后自动跑一遍该模块的「前5分钟走查」确认无副作用

### 边界（不加细节限制）
- 工具链不做「什么决策需要回滚」的判断——那是用户/替身的事，工具只保证「想回滚随时能回滚」

---

## 三、与用户替身的接口

- 账本中的 correction/feedback 条目 = 替身蒸馏的**唯一合法输入源**（可核实、带证据、带时间）
- 替身每次更新输出版本号+依据清单，和账本互相印证

---

## 四、工作量估算

| 项 | 估算 |
|----|------|
| ledger 模块（JSONL 读写 + record/show/audit CLI） | 1.5h |
| 回滚点自动生成（git 前置钩子脚本 + DB 快照） | 1.5h |
| rollback CLI + 状态流转 | 1h |
| 替身蒸馏脚本（从账本 correction 条目抽取 → 模型输入） | 1.5h |
| 集成进 server.py / 项目脚本 | 0.5h |
| **合计** | ~6h |

## 五、试点

- 先挂 video_editor_mvp（素材扫描模块开发期间全程记账）
- 跑通后推广到 4 Agent 通用（Kitty 的 OPC 机制层）
