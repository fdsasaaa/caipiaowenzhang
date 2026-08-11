# 老财迷文章生成流水线

目标不是“先让AI写，再看看能不能用”，而是在正文生成前把规则、案例、SEO和去重条件确定下来。

## 1. Topic planning

输入：

- provider_id
- lottery
- play
- 目标数量

规划器读取：

- 759个方法家族
- mechanics / economics 规则
- 已有文章Registry
- 技巧语义与案例算法

输出候选 angle。

## 2. Blueprint gate

每个候选 angle 转为 `article_blueprint`，至少固定：

- article_id / blueprint_id
- provider / lottery / play
- technique family / technique atoms
- title / primary keyword / secondary keywords
- search intent
- information gain type
- outline
- case structure / case plan
- rule refs / source refs
- fingerprint

此时不生成长正文。

## 3. Pre-draft dedup

蓝图必须先与 `registry/articles.jsonl` 比较：

- fingerprint 完全一致：直接拒绝；
- 核心标题、搜索意图、玩法、技巧原子、案例结构高度重叠：拒绝或重新选角度；
- 同一批蓝图 fingerprint 重复：只保留一个。

## 4. Reservation

通过 `blueprints --reserve` 后，ready blueprint 以 `status=idea` 写入文章Registry。

这意味着：**即使文章还没有写完，这个内容角度也已经被系统记住。**

未来生成任务必须把 idea / draft / approved / published 全部视为去重历史，而不是只查公开文章。

## 5. Draft generation

正文生成器未来必须严格使用蓝图，不允许临时替换：

- 玩法
- 核心技巧
- 搜索意图
- 案例算法
- 规则引用

正文语言要求：简单、短段落、先讲清方法，再给案例。

## 6. Case generation

若 `case_plan.case_engine_ready=false`，不得自动生成“技术案例”，必须先补齐技巧原子的算法定义。

若 ready：

- historical case：读取有来源的历史数据；
- illustrative case：构造简单数字，仅用于说明算法；
- synthetic validation：程序枚举或模拟检查公式。

所有普通案例默认 `predictive_guarantee=false`。

## 7. Quality + SEO gate

草稿至少复核：

- mechanics 是否匹配；
- 涉及金额时 economics 是否匹配；
- 是否出现稳赚/必中等确定性表述；
- 案例能否复算；
- 是否与Registry中新旧文章高度重叠；
- 标题、H1、Meta、搜索意图、内链建议是否完整；
- 是否真正增加了信息，而不是关键词换皮。

## 8. Approved package

通过后形成 `schemas/publish_package.schema.json` 定义的 package，交给 `fdsasaaa/xyptdq`。

网站仓库负责映射到迅睿CMS草稿，而不是内容引擎直接写生产数据库。

## 9. Publication memory

正式发布后，把：

- 最终标题
- URL
- 发布时间
- 最终内容Hash
- 技巧组合
- fingerprint

回写文章Registry，完成闭环。
