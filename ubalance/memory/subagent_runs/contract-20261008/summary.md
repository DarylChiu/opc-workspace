# Task Summary — contract-20261008

- **任务**: 越南合同扫描件 OCR + 角色与义务结构化提取（Balance 的 FOC 专案）
- **执行**: 子代理 `contract-20261008`（Balance）
- **日期**: 2026-10-08
- **模型**: deepseek/deepseek-v4-flash（如实标注）
- **输入**: `33_POWER_EXCELLENCE_INTERNATIONAL_LIMITED_CÔNG TY TNHH VIET GLORY.pdf`（12 页 RICOH 扫描件，无文本层）
- **工具**: pdftoppm（300dpi 渲染）+ 本机 tesseract（vie+chi_sim+eng, --psm 6）——**未使用云端多模态**

## 产出
1. `work/FOC业务场景/合同-33-POWER-EXCELLENCE-VIET-GLORY-OCR-20261008.md` — 逐页 OCR 原文（12 页）
2. `work/FOC业务场景/合同-角色与义务映射-20261008.md` — 主体表 / 条款清单 / 事实清单 / 桶 A·B 相关性 / 存疑清单
3. `memory/subagent_runs/contract-20261008/execution_trace.jsonl` — 15 步审计链

## 核心结论（事实层）
- 合同性质：**Hợp đồng thương mại / 贸易合同**（货物买卖），No. **02012026/VG-HT**，签署日 **2026-01-02**，有效期至 **2026-12-31**；非加工合同本身。
- 三方角色：**A=Power Excellence（买方）｜B=Hua Feng Group（卖方）｜HUATEX = B 的加工方（合同称「B方加工方代表」，非独立签约方，合同无「Bên C」定义）**。另有 A 的加工方 = Viet Glory。
- 换货/费用：不符样/质量差 → **B 换货并担全部费用**；换货期 3–5 天；不足量 B 立即补足担费；赔偿/违约金从货款扣除。
- **无「bảo hành（保修）」条款**；机制是「对样验收 + 换货 + 减价」，数量/外观异议期 **15 天**。
- 报关/开票：转厂/就地进出口；**HUATEX（B 加工方）出 VAT 发票 + 报关单**，Viet Glory（A 加工方）办进口。
- 付款：**A→B 离岸美元**（含 5% 折扣）；**HUATEX 与 Viet Glory 明确无付款责任**。
- 已验证否定事实：全文无 FOC/免费/赠与字样、无供料条款、无所有权/风险转移条款。

## 存疑要点（Top 3）
1. 交易标的 OCR 为「vải（面料）」，与 FOC 毛巾/家纺语境不符，需人工核对原件。
2. 合同无「Bên C」定义，HUATEX 独立主体地位无法从本合同验证（可能在上游 HFHT-2025/01，未随附）。
3. 合同无「bảo hành」措辞——桶 B 若靠「保修」定性，本合同文本不支持，只支持「来料不符/换货」。

## 纪律遵守
- 未臆测（不确定处标 `[存疑]`，缺失处写「未约定」）
- 未修改任何已有交付件（`deliverables/`、`FOC处理方案-v1-20261007.*` 原样）
- 未做税务定性结论（留待 Balance 主 Agent）
