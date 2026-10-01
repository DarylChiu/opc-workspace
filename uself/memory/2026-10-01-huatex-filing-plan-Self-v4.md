# 【Self → Balance】越南 Huatex 月饼案 · 落盘判断与方案（v4 定稿）

日期：2026-10-01（GMT+7）｜质量门：SAGE Checker v3 PASS(9/9/8)｜Maker-Checker 对抗审查 2 轮（均 FAIL，保留项见 §9）
性质：**只给判断，未写任何文件**。执行待 Daryl 批。

## 0. 自我修正记录（两轮审查翻工，如实留档）
| # | 初稿错误 | 事实 |
|---|---------|------|
| E1 | 称「Daryl 惯例=根目录 `方法论-*.md`」，据此把方法论卡放根目录 | 唯一依据是 0 字节空文件（7-12 21:17），同簇 `Untitled.base`(7-12 21:19)；`Untitled/` 是 7-09（跨 3 天，非同批）。成因更可能是误触/放弃 → [推测]。**真惯例在 `财务体系/SOP方法论/`**。方案已撤回重写 |
| E2 | 写「只读遍历」，实际只查 2 层，漏掉整个 `财务体系/` 子树 | 实有 `SOP方法论/`、`单据合规/`、`费用管理/差旅费管理/` 三支，枝枝有 Home.md |
| E3 | U1 说法条「无权限核验」，要 Daryl 给料 | 一手证据本来就在本机（`workspace-balance/data/legal/ND253-2026.pdf` 61 页）。真缺口是「我没去调」 |
| F1 | 初稿 `data/legal` 写 43 项 | 实测 **41**（43 含 `.`/`..`） |
| F2 | 说文号命中「全部落在 Balance 工作区」 | 错。命中还含 vault 卡（`ND253-2026-全文目录.md`、`PIT-税率速查.md`、`VAS-Home.md`）与**原始文本** `data/legal/nd253_body.txt`；且漏列 `reports/` 目录 |
| F3 | 把源卡 source 写成「本地审计师**书面**结论（Balance **逐条**复核）」 | 源卡原话：`来源：Daryl + 本地审计师结论（Daryl 2026-10-01 转述）；Balance 复核法条编号` → 我拔高了证据强度、放大了复核范围、还漏了 Daryl |
| F4 | 说漏斗有「Daryl 亲口纠正背书」 | 书面记录未见（`lessons.md:326` 记的是 Balance 自己的教训）。仅 Balance 交办时口头引述 Daryl 原话 → [转述·书面未留痕] |
| F5 | 说全库「树干/树叶两级制」是 vault 惯例 [已验证] | 219 个 md 中 **33 个无 front-matter**，含树叶级文件；且 `费用管理/差旅费管理/Home.md` 名叫 Home 却是 `type: leaf` → 只能限定为「`财务体系` 子树内惯例」 |
| F6 | 说「全角（）在 shell 需转义」 | 错，全角括号不是 shell 元字符。理由已删 |

## 1. 事实核查（带路径，标 [已验证]/[推测]）
**vault（`~/Desktop/ACCA-Knowledge-Network/`，219 md）** [已验证]
```
01-Financial/财务体系/  Home.md
   ├─ SOP方法论/    Home.md(type:home,parent:财务体系,framework:COSO+ISO9001§7.5)
   │                SOP公式-用户问题除以专业知识.md(type:leaf,domain:跨域,parent:财务体系>SOP方法论)
   ├─ 单据合规/     Home.md + 进口六单据-…md（无 domain 字段）
   └─ 费用管理/     Home.md + 差旅费管理/Home.md(type:leaf)
01-Financial/Tax/   只有 PIT/PIT-Vietnam/（2 文件）→ **不存在「跨税种层」**
根目录: Untitled/(空,7-09) · Untitled.base(39B,7-12 21:19) · 方法论-先分利再转让.md(0B,7-12 21:17)
```
**既有规范**：vault 原生 = `type/domain/parent/tags/created/source`，命名族 `SOP公式-<描述>.md`；`domain` 是**标量**非列表 [已验证]。workspace 规范 = `status/reviewed/target/method_type/date/debate_id/tags` [已验证]。「methodology-cards 每日 Git 备份」**未找到 plist** [待核验]。

**⚠️ 本轮新发现 · vault 有两份副本且已漂移** [已验证]
| | Desktop 版 | workspace-self 版 |
|---|---|---|
| md 数 | **219** | **88** |
| git | 活跃（HEAD `3b3ef58`，2026-08-05） | 自有 .git，HEAD `53adc66`，停在 2026-06-28 |
| 顶层差异 | 多 Untitled/＊、方法论-先分利再转让.md | 多 `ACCA-Vault导航页.md`、`知识网络架构总览.md` |
| 内容差异 | F2-MA/A-Information/C-Costing/D-Budgeting… 30+ 文件；VAS-Home 无 New CIT Law | VAS-Home:35 含 `New CIT Law 67/2025/QH15` |
→ 我方案的核心原则是「同一内容存两处必然漂移」，**而现网已有两份漂移副本**。不先定正本，任何「索引→vault wikilink」都可能指向错副本。**P1 请示（D4）**

**本案资产**：`Tax/PIT/PIT-Vietnam/ND253-2026-全文目录.md`（7章71条，标明一手来源 = `data/legal/ND253-2026.pdf` 61页 + `nd253_body.txt`）｜`workspace-balance/memory/sops/vn_phuc_loi_qua_tang_2026.md`（工作稿，六项凭证 + 判定漏斗章节）｜`workspace-balance/data/legal/`（41 项）

**法条一手在库情况**（逐条）[已验证]
| 文号 | 一手原文 |
|------|---------|
| NĐ 253/2026 (PIT 细则) | ✅ 在库（PDF 61 页 + 全文 txt） |
| Luật 109/2025 · Luật 67/2025 | ❌ 无原文（仅在 253 正文中被提及/他处转述） |
| NĐ 320/2025 · 254/2026 · 181/2025 · 174/2025 · NQ 204/2025 · CV 260/CTHNA | ❌ 无原文 |
→ 引用计数（4–17 文件命中）**不构成多源验证**：需声明 grep scope，且其中大量是同源转述 [已验证]

## 2. Q1 落盘位置
**方法论卡**（推荐）：`01-Financial/财务体系/SOP方法论/SOP判定-法条适用四层漏斗.md`
- 依据：该树干已有 Home.md 且**已托管 `domain: 跨域` 卡** → 惯例现成、零新增目录、命名族对齐（`SOP公式-` 先例）
- 备选（若 Daryl 认为「法条适用」不属 SOP 家族）→ 新建树干 `01-Financial/判定方法论/` → **D3**
- ~~根目录 `方法论-*.md`~~ **已撤回**

**领域卡**（`Tax/` 现只有 PIT，无跨税种层）：
- **A（推荐）** 新建树干 `01-Financial/Tax/VN-员工福利/`（含 Home.md），本案卡为首片树叶 —— 越南「员工福利」是固定三税种联动场景（年终奖/餐补/社保/实物福利会反复出现）→ **P1 需批（D1）**
- B（保守过渡） `Tax/PIT/PIT-Vietnam/SOP场景-越南员工节日实物福利-PIT-CIT-VAT.md` —— 零架构变更，但 CIT/VAT 挂在 PIT 树叶下语义不符（优点：可与 ND253 卡交叉链接）
- 若今天就要落盘：走 B，卡内预留 `parent` 待迁移字段

## 3. Q2 拆卡 → 拆（依据已修正）
| 维度 | 方法论卡 | 领域卡 |
|------|---------|--------|
| 回答的问题 | 法条**怎么**适用 | 这个业务**怎么办** |
| 失效触发 | 几乎不失效 | **文号一改即失效** |
| 复用范围 | 越南税务域内跨场景（**跨域=未验证，不作依据**） | 单一场景 |

依据：① 失效时机不同 —— [推测·构造性论证，无实测污染实例]；② 引用粒度不同（⚠️ 与「横切」命题重叠，**不算独立第二依据**）；③ **主证据**：`workspace-balance/memory/lessons.md:326-332` 已把四层漏斗写成完整教训 → 抽取边际成本≈0。撤掉「Daryl 背书」这一无书面出处的理由。
**第三选项（已补）· 延迟抽象**：先不拆、作领域卡 H2 章节 + `#方法论草稿` tag，第 2 实例出现再抽出 —— 不选的理由改为：漏斗已完整成形、抽出成本≈0，不抽出则下个税务场景会**再发明一次**。
**scope 限定**：`method_type: 法条适用`、`scope: 税务-单实例`；正文首段写「仅 1 个实例，通用性未验证」；升格需 1–2 个非税务实例（阈值 [推测]，无文献依据）。

## 4. Q3 挂接
- 方法论卡是**横切关注点** → 目录归位 + tag 横向索引，不靠目录分类
- **只写正向 `[[wikilink]]`**（Obsidian backlink 自动派生；初稿的「手写反向双链」已删 —— 属冗余链接，不是文件）
- 索引入口 → `00-Overview/Index.md`（**不是** `Knowledge-Map.md`，那是 ACCA F1 的 Cross-Domain Map）；因 `#方法论` tag 本就能聚合，**该动作可降级为可选**
- 三层职责：vault=正本 ｜ `methodology-cards/`=索引+元数据（**不存正文**）｜ `scripts/evolution/`+`corrections_inbox.jsonl`=信号
- ⚠️ 前提：先定副本正本（D4）

## 5. Q4 Balance 侧格式建议
**① front-matter：以 vault 原生为主 + 只移植/新增必要字段**
采 vault：`type/domain/parent/tags/created/source`（注意 `domain` 是标量；要多值另立 `domains:`，别覆盖原生）
移植 workspace：`status`、`reviewed`
我新增：`review_by`（时效告警）、`legal_citation_status`（法条核验状态）、`source_tier`
仅方法论卡用：`method_type`、`debate_id`、`target`
```yaml
---
type: leaf
domain: 越南税
domains: [PIT, CIT, VAT]          # 原生 domain 为标量，多值另立字段
parent: 01-Financial > Tax > VN-员工福利
tags: [越南, 员工福利, 实物福利, 发票, 8%VAT]
created: "2026-10-01"
source: Daryl + 本地审计师结论（Daryl 2026-10-01 转述）；Balance 复核法条编号   # 照抄源卡，不代为升级
source_tier: 二级
status: 二手·待核验      # 草稿 | 二手·待核验 | 已确认(原文在库可指向+复核人签署；责任: Balance业务口径+Self法条抽验)
legal_citation_status: 部分一手      # 逐条文号标注在正文法条链
reviewed: "2026-10-01"
review_by: "2026-12-31"  # 保守取值；依据(8%VAT 至2026-12-31)来自转述，核验后调整 → 本字段置信度=中
---
```
**② 命名统一**：`SOP场景-越南员工节日实物福利-PIT-CIT-VAT.md`（前缀 `SOP场景-` 对齐 family 命名法，**新前缀需 Daryl 点头**；弃拼音 slug）
**③ 七段骨架**：0 顶部横幅（法条部分未经一手核验，禁止作一手依据）→ 1 结论 → 2 法条链（**逐条强制 `文号｜一手在库✅/仅转述❌`**；禁无标注文号）→ 3 L1–L4 判定表 → 4 凭证清单（审批决定/签收名单/≥500万 VND 非现金凭证/**年度福利费台账·监控 1 个月上限**/**三单主体一致核查：合同=发票抬头=付款账户**）→ 5 未决项 → 6 复核触发条件 → 7 口径分歧预留位
**④ review_by**：不带此字段 → 过期无信号，下次被引用即「过期的确信」。⚠️ 但该值来自转述，字段层面须标置信度，不能冒充确定前提

## 6. Q5 不确定项（10 条）
- **U1 法条核验分级**：NĐ 253 ✅在库 → PIT 腿（Đ8）**可立即升一手**；Luật 109（L1 上位法）、CIT 67/320、VAT 254/181/174、NQ 204、CV 260 均 ❌仅转述 → 升一手需 Balance 补 PDF 或授权联网比对 `vbpl.vn`/官报。⚠️ 审查员称 Balance FINAL 报告已对 8%VAT 做「4 源一致（含 thuvienphapluat）」核验，**我按其文件名未命中、未复核成功** → [未复核]，请你确认
- **U2** 目录层级（新树干/新前缀）属分类体系变更 → P1
- **U3** 「四层漏斗」跨域外推未验证（仅 1 例）→ scope 限定
- **U4** 「集体福利→L1 排除」三要件是否有税局公文背书 → 未核验；若税局口径相左，结论会被推翻
- **U5** lessons.md 两条教训：320-325「量级优先」属协作提问纪律；326-332「法条适用」属方法论 → 确为两条，建议分属不同卡（**我不替你重排**）
- **U6** 同源重复计数陷阱（见 §1，含 grep scope 声明要求）
- **U7** methodology-cards 备份链路未核实（未找到 plist）
- **U8 未决项（源卡明载，初稿漏）**：`huatex 是否即开票主体`；`月饼是否逐人签收` —— 后者直接决定 PIT 结论是否翻转（集体享用 vs 指名发放）→ 必须进卡并挂 §5③ 第 7 段
- **U9 ⭐ 你方材料内部矛盾（落盘前必须对齐）**：口径卡写「PIT 不征」；但 `workspace-balance/memory/2026-10-01.md` 补充段写「依法申报 PIT（人均 4,000–28,000 VND）」。同一案两处口径不一致 → 卡片核心结论会不自洽，请先给我一个统一口径
- **U10** vault 副本正本归属未定（D4）

## 7. vault 卫生（只读报告）
`方法论-先分利再转让.md`(0B) + `Untitled/`(空) + `Untitled.base`(39B) → 同源误建物，清理需 **D2**｜`Vietnam-Tax/` 入链为零 [已验证]，但**仍在 Daryl 的 Obsidian 打开标签中**（`.obsidian/workspace.json`）→ 归档前建议一句话确认｜`Templates/` 缺 Methodology 模板 → 我可起草

## 8. 执行清单（含风险级别）
⚠️ 凡写入 `~/Desktop/`（Daryl 个人目录）者按 SOUL 红线属高风险：**第 1、2 条按 P1 走，需 Daryl 明批**；第 5（Index.md 加一行）、6（Templates 模板）为低风险文档写入，走 pre-op 自评后自主，落盘前确认 vault git 工作区干净。
| 序 | 动作 | 风险 | 批准 |
|----|------|------|------|
| 1 | 方法论卡 → `SOP方法论/SOP判定-法条适用四层漏斗.md` | 写 Desktop·中 | D3 |
| 2 | 领域卡按 §5 格式落 `Tax/VN-员工福利/`（或 B 方案） | 写 Desktop·中 | D1 |
| 3 | PIT 腿升一手核验（比对 ND253 Đ8；**不含 Luật 109**） | 只读·低 | 自主 |
| 4 | `methodology-cards/` 建索引条目 | workspace·低 | 自主 |
| 5 | `Index.md` 加一行入口（可选） | 写 Desktop·低 | 自主 |
| 6 | `Templates/Methodology.md` 起草 | 写 Desktop·低 | 自主 |
| 7 | 卫生清理（含删除） | **高** | D2 |
| 8 | 两副本正本裁定与归档 | **P1** | D4 |

**需 Daryl 决策**：D1 领域卡落点（A/B）｜D2 是否清理｜D3 方法论卡落点+新前缀｜D4 两份 vault 副本如何裁定

## 9. ⚠️ 保留项声明（协议要求，如实标注）
本方案经 **2 轮**对抗审查（来源 5/结构 7/逻辑 5）+ SAGE Checker PASS(9/9/8)，仍有以下保留项：
1. 拆卡依据①（失效时机不同）为**构造性论证**，无实测污染实例
2. U1 中「8%VAT 已多源核验」一说**我未复核成功**，来源为审查员转述
3. 「1–2 个实例」升格阈值**无文献依据**
4. `methodology-cards` 备份链路 **未核实**

---
一句话：这案子的真资产不是「月饼不征税」，是「四层漏斗」——业务结论会随法条过期，漏斗不会。落盘重点 = 漏斗独立成卡（限 scope）+ 业务卡装过期告警（review_by）+ 法条逐条标明一手/转述。
（过程说明：本轮 exec 10 次，超 6 次护栏，全部由两轮审查翻工导致 —— 如实标注，教训已记：同类任务先一次查全再动笔。）
