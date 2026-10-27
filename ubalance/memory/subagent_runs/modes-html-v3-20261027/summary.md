# v3 单文件 HTML · 执行摘要

**任务**：在 v2 基础上改单文件 HTML → v3（只做 HTML，不动 Excel）
**产出**：`deliverables/华特经营模式-交互图解-v3-20261027.html`（112KB / 2373 行 / 零外链 / 离线可用）
**中间件**：`work/huatex-modes-html-v3/`（head.html / modes.js / app.js / build.html / test.js / geom.js / probe*.html / dom*.html / shot-*.png / print.pdf）
**Trace**：`memory/subagent_runs/modes-html-v3-20261027/execution_trace.jsonl`（22 步）

## 四条修改怎么落地

1. **删预设**：PRESETS 数组 / renderPresets / applyPreset / presetId / .presets 样式 / 左侧预设面板 全部移除；boot 不再 applyPreset，初始四槽位全空。全文 grep「预设/preset」= 0。
2. **2/3/4 方**：仅 seller/buyer 必填；`effectiveRoles()` 补位（销售方=Huatex → 供货方默认 Huatex；收货方空 → 默认同购买方）；`contractShape()` 按补位后实际参与主体去重计数 → 双方/三方/四方徽标实时更新；引擎未定义也出图（虚线辅助节点补齐缺失主体，保证节点数=2/3/4）。
3. **待维护项**：加工（织造/染整/制造费用率）、物流 6 档、采购附加 4 档默认 `v:null`；成本树显示「— 待维护」灰字、不计入；总成本旁 + 成本树底两处提示；维护抽屉里清空输入即回 null。
4. **采购材料**：删「供应形态」及三取值；改为采购材料（纱线/胚布/成品布）× 采购方式（本地/A12/E31/A42）；料价/关税/反倾销按材料取参（1.65/2.30/3.20、3%/12%/12%、7.8%/0/0）；成本树改 ①采购②税费③加工④物流⑤采购附加。

## 验证结果（全部真跑）

- `node --check`：抽取交付文件 `<script>`（1892 行）→ 语法通过
- headless 断言：**70 / 70 PASS**（初始状态、7 类合同结构场景、成本手算、localStorage 往返、抽屉 5 tab、点选填槽位交互）
- 几何自检：7 场景节点重叠 0 / 越界 0 / 主体节点数 2-2-3-3-4-3-2 全对
- 外链扫描：`src=`0 `href=`0 `@import`0 `http`0；唯一 `url(` 为 SVG 内部 marker 锚点
- OCR（chi_sim）：读出标题、合同结构徽标（待填角色/双方/三方/四方）、`单位总成本 1.6995`、`— 待维护`、`加工成本/物流成本/采购附加尚未维护，当前总成本仅含采购成本＋税费成本`
- 打印 PDF 生成成功；420px 视口无横向溢出

## 未解决/占位

- 加工工费、物流 6 档、采购附加 4 档：**默认空**，需财务按实际维护
- 胚布/成品布反倾销率、进口关税（3/12/12%）：仍为占位，待按 HS 核实
- S1-09 报关单出口方写谁：待关务确认
- v3 新增 1 条规则（境外销售方+Huatex 供货+境外买方自收货→Huatex 侧离境出口），属工程性补规则，口径需业务确认
