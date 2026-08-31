# 文章标题 SEO 生成与验收规范 V1.0

## 1. 目标与边界

本规范只负责 `fdsasaaa/caipiaowenzhang` 的文章正文标题生产与验收，不改变现有文章生产、Approval、Approved parent、public-r1、库存或网站发布职责。

文章仓库负责：正文完成后的候选标题生成、最终标题选择、标题真实性与差异化 Gate、Approved/public-r1 中标题元数据留痕。

网站仓库 `fdsasaaa/xyptdq` 继续负责：网站关键词架构、跨页面最终冲突复核、首页/分类页展示、内链、Sitemap、搜索表现和正式接入后的 SEO 验收。本规范不得触发 CMS、Publisher、schedule、cron 或网站结构修改。

## 2. 标题生成顺序

标题编辑发生在正文完成之后。Blueprint / Article Angle 中原有 `title` 只视为工作标题和主题提示，不再拥有最终标题权。

每篇新文章必须：

1. 完成正文、summary、search_intent 与 claim_evidence；
2. 基于正文真实主题生成 3–5 个候选标题；
3. 候选标题至少覆盖 3 种不同表达结构；
4. 至少 2 个候选不得以彩种名开头；
5. 本地 Title SEO Gate 对候选进行真实性、相关性、重复度、搜索意图和可读性检查；
6. 只从通过规则的候选中选最终标题；
7. `title` 与 `seo_title` 使用同一个最终标题；
8. 保存 `title_candidates`、`title_selection_reason`、`title_review` 与 `title_seo_contract_version=1.0`。

Primary Keyword 仍然是不可随意改变的 SEO 所有权元数据，但不再要求逐字出现在最终标题里，也不要求位于标题开头。

## 3. 内容原则

最终标题必须准确扣住正文真正回答的问题，不做标题党。可以使用问题、对比、复盘、风险、结论、计算、成本、注数、周期、样本量等具体信息，但任何数字必须能够回到正文、claim_evidence、已验证规则或机器计算事实。

禁止为了点击率虚构命中率、收益、盈利天数、样本结果或社会证明。例如正文没有证据时，不得把“95%命中率”“2555元收益”“连续3天盈利”“90%的人不知道”写成事实。

标题如果讨论一个未经证实的数字说法，正文必须真实讨论该说法及其证据边界；疑问句只能改变陈述语气，不能凭空制造一个正文没有出现的数字。

## 4. 结构多样性

禁止把以下结构当成批量模板：

- `分分彩投注技巧：XXX`
- `分分彩技巧：XXX`
- `分分彩方法：XXX`
- `分分彩教程：XXX`
- `exact Primary Keyword：固定解释句`

允许“分分彩”出现在标题前部、中部、尾部，也允许长尾标题完全不出现“分分彩”。最终目标是让标题像真人编辑根据每篇正文重新拟定，而不是把关键词字段拼接成标题。

可混合的问题型、计算型、复盘型、对比型、风险型、结论型、步骤型和解释型结构，但任何示例都不是固定模板。

## 5. 强制 Gate

新文章进入 Approval 前、public-r1 公开版形成时，都必须通过以下关键 Gate：

### `TITLE_TOPIC_MATCH`

标题必须保留文章的具体玩法、技术原子、计算问题或研究问题，不能把正文写 A、标题写 B。

### `TITLE_DUPLICATION_CHECK`

最终标题与正式 Approved/public-r1 标题做相似度检查。V1.0 硬阈值为 `0.84`；达到或超过阈值即拒绝。审计预警阈值为 `0.78`。

### `TITLE_KEYWORD_DIVERSITY`

候选 3–5 个且不得重复；至少 3 种标题结构；至少 2 个候选不以彩种名开头；最终标题必须来自候选集合；禁止机械使用 exact Primary Keyword 作为冒号前缀，禁止通用“投注技巧/技巧/方法/教程”批量前缀。

### `TITLE_NUMERIC_CLAIM_VERIFIED`

标题中的数字、百分比、期数、金额、注数、组数、层数、倍数、天数等必须能在正文、claim_evidence 或机器合同事实中找到对应依据。没有依据即拒绝。

### `TITLE_SEARCH_INTENT_CHECK`

标题必须表达该文章已经确定的 search intent，而不是仅仅包含一个热门词。

### `TITLE_CLICKABILITY_CHECK`

标题需要自然、具体、易理解，有明确的问题、对比、数字、风险、复盘、边界或结论钩子；同时禁止关键词堆砌、夸张承诺和保证性语言。

任何关键 Gate 不通过，都不得为了达到每日 10/20/25 库存目标而放行；`quality_floor_lowering_allowed=false`。

## 6. Approved 与 public-r1

Approved parent 一旦正式落库继续保持 immutable。本次标题审计不得直接批量改写现有 Approved parent。

未来新 Approved 必须保留 Title SEO V1.0 的审计元数据。public-r1 在公开改写正文之后必须再次生成/选择公开版候选标题并重新过 Gate，因为公开改写可能改变正文重心。

对历史正式文章，如标题审计建议修改，只能走明确的 revision 路径；不得覆盖原 Approved parent，也不得伪造旧 revision/hash。

## 7. 现有库存审计

审计对象只认 `main` 上正式 `articles/public_release/*/*.public-r*.json` 的最新 revision。审计只输出问题、相似度、数字证据状态和 3 个候选标题，不直接修改正文或正式文章文件。

机器报告：`agent/results/TITLE_SEO_AUDIT_2026-08-24.json`

人工报告：`agent/results/TITLE_SEO_AUDIT_2026-08-24.md`

## 8. 长期扩展原则

标题系统面向数百、数千篇库存设计：Primary Keyword 负责所有权，标题负责真人可读的搜索入口；标题差异化不能靠随机换同义词，而要来自文章真正不同的读者问题、玩法、实验、数学、风险或结论。
