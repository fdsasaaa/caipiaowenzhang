# 老财迷彩票内容引擎（caipiaowenzhang）

这是 `laocaimi.org` 的独立内容研发仓库。它负责 Research/Content，不直接承担生产网站运行。

## 当前版本

`v0.5.0-analysis-case-engine`

当前基础资产：

- 2406 个 brbcw 精选来源ID，可重建原始公开URL
- 2294 篇能识别出明确技巧原子
- 759 个方法家族，作为未来文章规划经验层
- 1389 个精细方法簇已完成抽取审计
- 1321 篇带盈利、百分比或保证性风险声明，统一隔离为来源声称
- Google SEO 官方政策快照与内容质量门禁
- 玩法机制 / 平台经济参数 双层规则系统
- 时时彩历史官方机制基线 + 前二/前三/中三/前四/后四位置同构规则
- 和值、跨度、频率、遗漏、奇偶、大小、重号、邻号等可执行分析指标
- 可复算文章案例引擎与案例Schema
- `caipiaowenzhang → fdsasaaa/xyptdq → www.laocaimi.org` 草稿发布协议

## 核心原则

1. **玩法机制与经济参数分开**：选号范围、投注格式、注数公式、中奖条件可以建立玩法规则；单注金额、奖金/赔率、返点、限额必须绑定具体平台。
2. **历史时时彩不是当前官方在售产品**：财政部等已要求高频快开彩票在2021年春节休市结束后全部停止销售。历史规则只作为玩法机制基线。
3. **分分彩等不得自动继承时时彩规则**：必须通过 provider/lottery/play 显式映射确认开奖结构与玩法判定一致。
4. **统计指标不是预测结论**：冷热只表示指定窗口频率，遗漏只表示距离上次出现的期数；和值、跨度等都是描述和筛选指标。
5. **来源文章不是事实库**：论坛文章中的命中率、稳赚、倍投收益只作为 `unverified_source`。
6. **禁止换皮重复**：标题不同但技巧原子、案例结构、搜索意图高度重合，也视为重复。
7. **案例必须可复算**：输入开奖、样本窗口、参数、计算过程、候选输出和规则引用必须能重现。
8. **SEO必须增加信息价值**：不通过同义改写、抓取拼接、关键词变体批量制造页面。
9. **生产隔离**：本仓库 → Approved Package → `fdsasaaa/xyptdq` → 迅睿CMS草稿 → `www.laocaimi.org`。

## 玩法机制层

历史官方基线：`rules/mechanics/ssc/`

当前核心覆盖：

- 一星直选 / 个位定位胆
- 后二直选、后三直选、五星直选
- 后二组选
- 后三组选3 / 组三
- 后三组选6 / 组六
- 单位置定位胆
- 后二大小单双

位置同构推导：`rules/mechanics/ssc_derived/`

- 前二直选 / 前二组选
- 前三直选 / 前三组选3 / 前三组选6
- 中三直选 / 中三组选3 / 中三组选6
- 前四直选 / 后四直选

这些推导只证明十进制固定位置的组合数学；目标平台是否真的提供同名玩法，仍必须通过 provider mapping 确认。

## 分析与案例层

`engine/analysis_metrics.py` 提供：

- `digit_sum`：和值
- `span`：跨度
- `frequency`：指定样本窗口频率
- `current_omission`：固定位置当前遗漏
- `parity_pattern`：奇偶结构
- `size_pattern`：大小结构
- `repeat_pattern`：重号 / 豹子 / 组三 / 组六
- `has_neighbor_pair`：邻号结构

`knowledge/TECHNIQUE_SEMANTICS.json` 规定每种技巧原子的计算定义和允许的文案边界。

`engine/casebook.py` 可以把一组按时间排序的五位开奖号码转成文章案例数据包；默认强制：

- `claim_scope = descriptive_only`
- `predictive_guarantee = false`

案例标准：`docs/ARTICLE_CASE_STANDARD.md`

## CLI 示例

```bash
python -m engine.cli audit
python -m engine.cli capability --provider <provider_id> --lottery 时时彩 --play 组三
python -m engine.cli plan --provider <provider_id> --lottery 时时彩 --play 组三 --count 10

python -m engine.cli case \
  --draw 12345 --draw 22346 --draw 92347 --draw 02348 \
  --selector 后三

python -m engine.cli omission-case \
  --draw 12345 --draw 22346 --draw 92347 --draw 02348 \
  --position 个位 --threshold 2

python -m engine.cli frequency-case \
  --draw 12345 --draw 22346 --draw 92347 --draw 02348 \
  --selector 后二 --lookback 4 --top 3
```

## 文章规划器

规划结果仍有三档：

- `blocked_mechanics_verification`：玩法机制未核验，只能保留选题想法。
- `ready_mechanics_only`：可写玩法、选号、注数和中奖条件案例，但不能陈述未核验的金额/奖金/返点。
- `ready_full`：玩法机制和具体平台经济参数都已核验，可以生成完整案例。

每个候选选题现在还会带 `case_plan`：

- 哪些 technique atoms 已有可执行指标；
- 应调用什么 metric；
- 哪些 atoms 仍 unsupported；
- 是否已具备自动案例生成条件。

这样未来生成器不能为缺少算法定义的技巧临时编造规则。

## Provider 映射

- `schemas/provider_lottery_mapping.schema.json`
- `mappings/PROVIDER_MAPPING_POLICY.md`

即使 mapping 为 verified，经济参数仍不得从历史时时彩继承。

## 知识层

- `knowledge/source_sets/`：2406个精选来源ID
- `knowledge/family_archives/brbcw_families_v1.part-*.b64`：759个方法家族紧凑知识档案
- `knowledge/coverage/brbcw.json`：整体覆盖统计
- `knowledge/coverage/brbcw_report.md`：人类可读审计报告
- `knowledge/TECHNIQUE_TAXONOMY.json`：技巧原子词典
- `knowledge/TECHNIQUE_SEMANTICS.json`：技巧原子计算语义

Git默认不保存2406篇论坛全文。需要回看案例时按来源ID定位原公开帖子。

## 发布层

- 网站仓库：`fdsasaaa/xyptdq`
- CMS：迅睿CMS
- `schemas/publish_package.schema.json`：内容引擎交付协议
- `schemas/article_case.schema.json`：文章案例协议
- `publishing/XYPTDQ_BRIDGE.md`：草稿发布边界与验收规则

发布后必须把最终URL、发布日期、最终标题、技巧组合和内容指纹回写 `registry/articles.jsonl`，永久参与后续去重。

## 测试

```bash
pytest -q
python -m engine.cli audit
```
