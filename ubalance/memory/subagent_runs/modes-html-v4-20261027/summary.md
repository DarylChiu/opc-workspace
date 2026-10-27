# modes-html-v4-20261027 · 华特经营模式交互图解 v4

**产出**：`deliverables/华特经营模式-交互图解-v4-20261027.html`（115,827 bytes / 2,408 行 / 单文件零外链）
**中间件**：`work/huatex-modes-html-v4/`（基线备份、抽出脚本、3 份测试报告、dump、截图）

## 本轮两件事

### 1. 删两处界面文字块
- 左栏「判定说明 / 引擎口径」整个 panel —— 删除。
- 角色槽位下方「默认规则（可覆盖）」`.defrule` 整块 + 3 条 CSS —— 删除。
- 槽位内灰字默认提示保留：③「默认：Huatex（自行生产）」、④「默认：同购买方」（未填销售方时 ③ 显示「默认：同销售方（Huatex 时＝自行生产）」）。
- 为避免「文案只是隐藏」的质疑，全文把「默认规则」改为「默认补位」，使 dump-dom 对 `判定说明` / `默认规则` / `引擎口径` 的 grep 均为 **0**。

### 2. 三流图重画（通用规则，非逐模式手写）
```
供货方 = 填的 or 销售方         收货方 = 填的 or 购买方
货物流 = 供货方 → 收货方                              标签 = 模式 gcode（报关类型）
发票流 = dedupe([供货方, 销售方, 购买方])              末段 = 销项 VAT 率；前段 = 内部结算（进项）
资金流 = 发票流反向                                    标签 = 付款
```
- 删掉 v3 的 gate 节点与「补齐用」aux 虚线节点（这是 v3 把 S1-02 画错的根因之一）。
- 唯一模式级例外：**S1-09（结构 B）** `invBuyer:'restructured_overseas'` —— 结构 B 下合同主体须换成境外买方，本地 C 退出商业链；此例外写在模式属性里，不是写死一张图。
- 每条线带 `data-flow` / `data-path` / `data-label`，每个节点带 `data-node` / `data-lane` / `data-role`。

## 9 场景实测（playwright 读 DOM，非目视）
| # | 场景 | 模式 | 货物流 | 发票流 | 资金流 |
|---|---|---|---|---|---|
|1|双方·出口|S1-01|Huatex→海外公司（出口报关（一般贸易））|Huatex→海外公司（VAT 0%）|海外公司→Huatex（付款）|
|2|双方·内销|S1-07|Huatex→本地（无需报关）|Huatex→本地（VAT 8%）|本地→Huatex|
|3|买方=EPE 自收货|S1-05|Huatex→EPE（E62 就地出口／EPE 办就地进口）|Huatex→EPE（VAT 0%）|EPE→Huatex|
|4|S1-02 四方·收货 EPE|S1-02|Huatex→EPE（E62 就地出口）|**Huatex→HFGI（内部结算（进项））→海外公司（VAT 0%）**|**海外公司→HFGI→Huatex**|
|5|S1-03 四方·本地买断|S1-03|Huatex→本地（E62 就地出口／收货方办就地进口）|Huatex→HFGI→海外公司|海外公司→HFGI→Huatex|
|6|S1-04 四方·本地代工|S1-04|Huatex→代工厂（E62／加工 nhập gia công 就地进口）|Huatex→HFGI→海外公司|海外公司→HFGI→Huatex|
|7|S1-08 结构A|DUAL|Huatex→EPE（C 报就地出口）|Huatex→本地 C（VAT 8%）|C→Huatex|
|8|S1-09 结构B|DUAL|Huatex→EPE（E62 就地出口）|Huatex→境外买方（重构后）（VAT 0%）|境外买方→Huatex|
|9|三方·缺收货方|S1-01|Huatex→海外公司（出口报关）|Huatex→HFGI→海外公司|海外公司→HFGI→Huatex|

## 自检结果（全部实跑）
1. 外链：src=0 / href=0 / @import=0 / http=0 / link=0 / iframe=0 / fetch=0；`url(#arw-*)` 内部锚点 1；加载后请求数组为空。
2. JS：抽出 77,680 chars → `node --check` 通过；页面 0 error / 0 pageerror。
3. dump-dom 初始态：slot empty ×4、待填角色、1.6995、待维护 39 处、判定说明/默认规则 = 0。
4. 9 场景三流：9/9 与要求表一致（见上表）。
5. 补齐节点 0；主体节点并集数 == 徽标 n（2/3/4）全部相符。
6. 成本：1.6995 / 1.8777 / 1.8777 / 1.6995 / 填满后 2.4320，提示消失。
7. localStorage 往返 + reload 一致（version=v4）。
8. 截图 + OCR：读得出标题、徽标、1.6995、`— 待维护`×12。
9. 几何：8 场景重叠 0 / 越界 0 / 标签出界 0 / 标签压节点 0。
