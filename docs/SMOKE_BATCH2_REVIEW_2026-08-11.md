# 第二批端到端内容烟测复盘（2026-08-11）

## 结果

第二批5篇文章已经完成：

`2406来源知识库 → Planner → verified rule binding → resolved selector → Blueprint → Draft Packet → AI Draft → Approval Pipeline → Approved Package → xyptdq ingress → website converter → content/drafts`

生产边界保持：

- 第二批网站 drafts：5篇
- 第一批 + 第二批网站 drafts：8篇
- `content/scheduled`：0篇
- Native Publisher：未调用
- CMS生产写入：未执行
- 公开发布：0篇

内容引擎第二批合并提交：`08d568a79d1d7bc64551261c9aacf2dd0e3fd961`

网站第二批草稿合并提交：`717fb1d73d8a4da6760b3d409c230817695d6f48`

## 五个真实来源家族

1. `FAM-32137acbb90340b9`
   - 来源：`BRBCW-003787`
   - support=6，risk=0.167
   - rule play：后二大小单双
   - selector：后二
   - atoms：`big_small_filter + odd_even_filter`

2. `FAM-66e3a5bb1e229e8a`
   - 来源：`BRBCW-008754`
   - support=11，risk=0.273
   - rule play：定位胆
   - selector：个位（deterministic example default）
   - atom：`cold_hot_split`

3. `FAM-c9d752aac7c51169`
   - 来源：`BRBCW-001458`
   - support=14，risk=0.5
   - rule play：后三组选3
   - selector：后三
   - atom：`sum_range`

4. `FAM-c93cfcc1527bf6f8`
   - 来源：`BRBCW-002590`
   - support=29，risk=0.379
   - rule play：后三直选
   - selector：后三
   - atoms：`position_filter + span_range`

5. `FAM-bee5958fb0d2f766`
   - 来源：`BRBCW-003939`
   - support=16，risk=0.562
   - rule play：定位胆
   - selector：个位（source position）
   - atoms：`omission_threshold + position_filter`

## v1.2 selector 修正为什么是必要的

第二批最初只有3个家族可以进入案例引擎。高支持的“位置+跨度”“位置+遗漏”等家族因为 `position_filter` 没有明确语义而被正确阻断。

在补语义时又发现旧逻辑存在更深的问题：来源家族可能带多个 `positions`，旧 Blueprint 曾可能取列表中的第一个位置作为案例 selector，即使目标玩法是“后三”。这会让文章标题讲后三，案例却按万位计算。

v1.2 改成：

`verified play → resolved_selector → case_plan → Blueprint → Draft Packet`

并规定：

- `position_filter` 只是计算作用域绑定，本身不是预测信号；
- 固定窗口玩法由玩法本身决定 selector；
- 来源位置不支持目标窗口时，该家族不能生成；
- 定位胆多位置来源拆成多个明确单位置候选；
- omission 只允许单位置；
- 和值、跨度必须使用合法号码窗口。

完成后五个目标家族均由独立 GitHub Actions 探针实机确认 `case_engine_ready=true`。

## 内容层边界

第二批第一次真正让2406篇来源知识库参与文章生产，但没有把来源文章原文或来源中的未经验证结论直接搬入正文。

正文只继承：

- 来源支持的方法家族；
- 技巧原子；
- 来源位置元数据；
- 已验证玩法机制；
- 可执行统计指标。

正文明确拒绝：

- 未验证的平台赔率、奖金、返点、最低投注单位；
- 来源文章中的“稳赚、必中、必赚”等保证性说法；
- 把冷热、遗漏、和值、跨度的历史结构直接解释成下一期概率优势。

## 案例原则

第二批案例统一使用由文章 fingerprint 决定的可复现 synthetic data，并明确标记：

`演示数据，不是真实开奖记录`

这样案例可以稳定复算，同时避免伪造真实开奖经历。

## 审批与跨仓库验证

内容引擎 CI 对5篇逐篇重新执行：

- Planner 从真实2406来源知识库寻找 family；
- 核对 source ID、support、risk、atoms；
- rule scope 保持 `时时彩` verified mechanics；
- subject scope 明确为 `分分彩`；
- 生成 Blueprint / Draft Packet；
- 执行真实 Approval Pipeline；
- quality ≥ 80；
- 与冻结 Approved Package 除 `approved_at` 外逐字段一致。

网站 CI 对5篇逐篇重新执行正式 converter，并验证：

- Approved Package content hash 正确；
- fingerprint 跨仓库不变；
- `tzjq/catid=3`；
- `publication_state=draft`；
- 无 `publish_at`；
- 无对应 `content/scheduled` 文件。

## 当前总状态

第一批3篇 + 第二批5篇 = **8篇已批准网站草稿**。

仍然：

- Scheduled：0
- Published：0
- Promote：未执行
- Native Publisher：未调用
- 生产CMS：未写入

## 下一步建议

当前最明显的内容缺口已经不是“能否生成文章”，而是**8篇之间的内链仍为空**。

下一步应先建立 Internal Link Planner：

- 只能链接 Registry 中已经存在且语义相关的文章；
- 根据 subject、play、technique atoms、search intent 和 information gain 计算关系；
- 防止自链、循环堆砌和无关SEO内链；
- 输出建议锚文本与目标 article_id；
- 先更新内容引擎 Approved Package，再由网站 converter 更新 drafts；
- 仍不进入 scheduled。

第一批和第二批已经形成可用关系，例如：

- 前三直选单式/复式格式 ↔ 后三直选跨度；
- 定位胆格式 ↔ 定位胆冷热 / 定位胆遗漏；
- 组选包胆注数 ↔ 后三组选3和值。
