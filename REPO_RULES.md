# OPC 统一仓库规则

> 仓库: https://github.com/DarylChiu/opc-workspace

## 📁 目录结构规则

**一级目录 = Agent 名，二级目录 = 项目名**

```
opc-workspace/
├── Bryson/              # 吹点小风（视频分析 + 雅思陪练）
│   ├── video-analyzer/  # 项目
│   ├── voice-mvp/       # 项目
│   └── ...
├── Kitty/               # 主 Agent（OPC 协调 + 看板）
│   └── ...
├── Balance/             # 成本控制 Agent
│   └── ...
├── Self/                # 知识管理 Agent
│   └── ...
└── Shared/              # 跨 Agent 共享资源
```

### 新建项目时
```bash
mkdir -p 你的Agent名/项目名
# 把代码放在里面
git add -A && git commit -m "新项目: 项目名" && git push
```

## ⚠️ 删除限制

**只有 Bryson 有权删除文件。** 任何人 push 的删除操作会被 GitHub Actions 自动拦截。

误删也不怕，push 时会被拒绝。

## 🔄 每日自动备份

每天 23:59 自动 `git pull --rebase && git add -A && git commit && git push`

即使忘了手动 push，也不会丢代码。

## 🏷️ 提交身份

| Agent | 提交方式 |
|-------|---------|
| Bryson | 直接 `git commit` |
| Kitty | 用 `scripts/kitty-git commit` |
| Self | 用 `scripts/self-git commit` |
| Balance | 用 `scripts/balance-git commit` |

## 🔑 仓库地址

- Web: https://github.com/DarylChiu/opc-workspace
- SSH: `git@github.com:DarylChiu/opc-workspace.git`
