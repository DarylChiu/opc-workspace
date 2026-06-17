# Project: OPC看板交互系统 (OPC Dashboard)

> 最后更新: 2026-06-17（视频分析MVP workflow部署）
> 仓库: /Users/zhaoyuzhao/WorkBuddy/Claw
> 转发记录源: feishu_forwards/forward_20260616_0956.md (6/5) + forward_20260616_1517.md (6/8) + forward_20260615_1044.md (6/12)
> 仓库: /Users/zhaoyuzhao/WorkBuddy/Claw
> 转发记录源: feishu_forwards/forward_20260616_0956.md (6/5) + forward_20260616_1517.md (6/8) + forward_20260615_1044.md (6/12)

---

## 一、Daryl 的完整需求清单（按优先级排列）

### P0 · 核心需求（M1必须实现）

1. **Agent状态+任务合并面板** — 2×2 四宫格，不滚动展示全部4个Agent
   - 每个Agent卡片显示：名称、角色、在线状态、当前模型
   - 卡片下方三列：📥待办 / 🔄进行中 / ✅已完成
   - 已完成任务 → 超链接跳转到「产物与预览」面板
   - 右上角「+」按钮 → 弹窗新建任务
   - 新建任务后 → **强制 Agent 飞书 DM Daryl 澄清确认后再开始执行**
   
2. **产物与预览面板** — 左右排列
   - 左侧：产物文件列表 + 类型过滤
   - 右侧：iframe 预览
   - 单击 → 预览；双击 → HTML 用浏览器打开，其他文件触发下载
   - **产物源仅限 OPC 专用目录**，不扫 WorkBuddy 全局目录
   
3. **Agent 状态实时** — 对接 OpenClaw API（30s 轮询起步）
   - 不能是静态 JSON 报告的过期快照
   
4. **项目进度** — 按 Agent 的核心开发项目披露
   - 小任务不在项目进度中显示
   - 里程碑时间线 + 进度条

### P1 · 基本需求（M1完成）

5. **左侧导航菜单**（最终顺序）：
   ```
   A. Agent状态和任务
   B. 产物与预览  
   C. Workflow 可视化编辑器
   D. 成本仪表盘
   E. 沙箱任务
   ```

6. **部署**：Ngrok Tunnel（弃用 Cloudflare）

7. **技术栈标注**：每次汇报说明用了什么模型/框架

### P2 · 功能需求（M2 实现）

8. **Workflow 可视化编辑器**
   - ComfyUI 风格：可拖拽节点 + 连线
   - 一个项目 = 一条 workflow，标注负责 Agent
   - 时间轴：每个环节预估/实际耗时
   - Daryl 可缩短预估驱动 Agent 调整方案
   - 实时同步：拖拽完 5s 内通知 Agent（WebSocket）
   - 已完成项目：只读，下次运行时 DM 确认 + 风险提示
   - 进行中项目：暂停 → DM 确认 + 提醒沉没成本

9. **成本仪表盘** — API 调用成本实时追踪

10. **沙箱任务** — 沙箱实例状态监控

---

## 二、明确不要的（Daryl 多次强调）

- ❌ 案例模版市场（WorkBuddy 商业模式，6/5 明确拒绝）
- ❌ 沉重的 SKILL 库管理（"对你来说太沉重了"，6/5 明确取消）
- ❌ 直接使用 WorkBuddy 全局工作目录作为产物源
- ❌ 静态报告文件作为 Agent 状态数据源（要实时）
- ❌ Cloudflare Tunnel（6/15 改 Ngrok）

---

## 三、开发流程铁律

> **以后开发项目没有梳理完核心需求和基本需求就不要开始，这样 Demo 出来可能都是沉没成本**（Daryl 6/16 重申）

- 项目开发计划必须先汇报，Daryl 确认后再开工（6/8 明确定）
- 汇报必须标注技术栈（6/8 要求）
- 双 Agent 开发时明确分工，不交叉修改同一文件（6/8 教训）
- 先做 localhost 验证，公网隧道最后一步完成（6/8 策略）

---

## 四、M1+M2 重建计划

### M1 · 核心看板上线（本次重建）

| 模块 | 内容 | 验收标准 |
|---|---|---|
| A. Agent状态+任务 | 四宫格 + 三列任务 + 新建任务 + DM通知 | 4Agent实时状态可见，新建任务触发DM |
| B. 产物与预览 | 左右布局 + 文件扫描 + iframe预览 | 单击预览有效，双击打开，无404 |
| 后端 | Node.js + Express + OpenClaw API对接 | /api/agents实时，/api/artifacts正确路径 |
| 部署 | localhost + Ngrok Tunnel | 公网可访问 |
| C/D/E 面板 | 占位骨架 | 导航可切换 |

### M2 · 功能完善（后续）

| 模块 | 内容 |
|---|---|
| C. Workflow | React Flow + WebSocket实时同步 |
| D. 成本仪表盘 | API成本API对接 |
| E. 沙箱任务 | 沙箱实例监控 |

---

## 五、技术栈

- 前端：HTML5 + CSS3 + Vanilla JS（零依赖）
- Workflow面板（M2）：React + React Flow
- 后端：Node.js + Express
- 实时通信（M2）：WebSocket (OpenClaw Gateway)
- 部署：Ngrok Tunnel
- Agent数据源：OpenClaw CLI/API（实时轮询）

---

## 六、每次迭代的关键需求记录

### 6/5 — WorkBuddy 调研与需求定位
- Daryl试用WorkBuddy，整体不适合但快速落地项目能力好
- 多次驳回我的方案：太简单→包含案例市场→过度简化
- 最终授权我直接检查本机WorkBuddy
- 明确：要HTML界面+产物预览+快速执行，不要案例市场+SKILL库

### 6/8 — M1开发 + V2验收
- 分工混乱 → Daryl明确Kitty前端/Bryson后端
- 没有参考WorkBuddy优势 → Daryl要求加入产物/预览/沙箱面板
- V2验收要求：四宫格、三列任务、产物预览修复、实时状态
- 新建任务→DM通知Daryl确认的流程

### 6/12 — Workflow模块需求
- ComfyUI风格节点编辑器
- 项目粒度workflow，Agent标注
- 实时同步（WebSocket）、时间轴、沉没成本提醒

### 6/15-16 — 部署调整与清理
- Cloudflare → Ngrok
- 产物目录限定
- 时间预算按实际调整
- 重新开发M1+M2

### 6/17 — 视频分析MVP Workflow部署（以Bryson项目为例）
- **Workflow 名称**：视频分析MVP V3.1
- **部署目标**：OPC看板 Panel C · Workflow 可视化编辑器
- **节点**：9个环节，按实际管道设计
  1. 📥 视频接入（xiaofeng, 6h, in_progress）
  2. 🎵 音频提取（xiaofeng, 4h, done）
  3. 📝 音频转写（xiaofeng, 12h, pending）⚠️ Bryson发现的盲区
  4. 🎬 关键帧抽取（xiaofeng, 8h, pending）
  5. 🧩 句子对齐采样（xiaofeng, 10h, pending）
  6. ⚡ 并行特征提取（xiaofeng, 12h, pending）
  7. 🧠 多模态分析（kitty, 10h, pending）
  8. 📊 结果整合（kitty, 6h, pending）
  9. 🔄 反馈闭环（xiaofeng, 4h, pending）
- **连线**：9条边，包含并行分支（音频转写+关键帧抽取并行）
- **预估总工时**：72h
- 存储位置：`opc-dashboard/data/workflows.json`
- API可用：`GET/POST /api/workflows`
- 前端已验证拖拽编辑+属性修改+保存
