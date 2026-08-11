# position_filter 与案例 Selector

从 v1.2.0 起，`position_filter` 被定义为**计算作用域绑定**，不是预测指标。

它回答的是：

> 后续和值、跨度、频率、遗漏等统计到底作用在哪个位置或窗口？

例如：

- 后三直选 → `selector=后三`
- 前二组选 → `selector=前二`
- 后二大小单双 → `selector=后二`
- 一星直选 → `selector=个位`

## 固定窗口玩法

目标玩法自身能够唯一确定窗口时，目标玩法优先。来源家族中 `positions` 的排列顺序不能改变案例 selector。

如果家族包含 `position_filter`，并且来源位置列表不支持目标窗口，该家族不会为该玩法生成候选。

## 定位胆

`定位胆` 本身没有唯一位置。

- 若来源家族明确包含万/千/百/十/个中的一个或多个位置，则 Planner 把每个单位置拆成独立候选；
- 若技巧本身不含 `position_filter` 且来源没有位置，例如通用冷热频率家族，案例默认用 `个位` 作为确定性的**演示位置**，并在 `selector_basis=deterministic_example_default` 中显式记录；这不是来源声称，也不是预测结论。

## 语义校验

每个技巧原子都可以限制合法 selector：

- `sum_range` / `span_range`：二星至五星窗口；
- `omission_threshold`：只允许万/千/百/十/个单位置；
- `position_filter`：允许所有已登记位置/窗口；
- 频率、奇偶、大小：在明确 selector 上计算。

`case_requirements()` 在 selector 未解析或与技巧不兼容时 fail-closed，`case_engine_ready=false`。

## 防止旧错位

旧逻辑曾可能把来源家族位置列表的第一个位置写入 `case_structure`，即使目标玩法是另一个窗口。v1.2 改为：

`verified play → resolved_selector → case_plan → Blueprint case_structure → Draft Packet case bundle`

因此案例计算和目标玩法使用同一个明确 selector。
