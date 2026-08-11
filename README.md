# 老财迷彩票内容引擎（caipiaowenzhang）

这是 `laocaimi.org` 的独立内容研发仓库。它负责 Research/Content，不直接承担生产网站运行。

## 当前版本

`v0.4.0-ssc-mechanics`

当前基础资产：

- 2406 个 brbcw 精选来源ID，可重建原始公开URL
- 2294 篇能识别出明确技巧原子
- 759 个方法家族，作为未来文章规划经验层
- 1389 个精细方法簇已完成抽取审计
- 1321 篇带盈利、百分比或保证性风险声明，统一隔离为来源声称
- Google SEO 官方政策快照与内容质量门禁
- 玩法机制 / 平台经济参数 双层规则系统
- 首批9类 时时彩 历史官方玩法机制基线
- `caipiaowenzhang → fdsasaaa/xyptdq → www.laocaimi.org` 草稿发布协议

## 核心原则

1. **玩法机制与经济参数分开**：选号范围、投注格式、注数公式、中奖条件可以建立玩法规则；单注金额、奖金/赔率、返点、限额必须绑定具体平台。
2. **历史时时彩不是当前官方在售产品**：财政部等已要求高频快开彩票在2021年春节休市结束后全部停止销售。历史规则只作为玩法机制基线。
3. **分分彩等不得自动继承时时彩规则**：必须通过 provider/lottery/play 显式映射确认开奖结构与玩法判定一致。
4. **来源文章不是事实库**：论坛文章中的命中率、稳赚、倍投收益只作为 `unverified_source`。
5. **禁止换皮重复**：标题不同但技巧原子、案例结构、搜索意图高度重合，也视为重复。
6. **案例必须可复算**：机制核验后可写选号、注数和中奖条件；只有 economics 核验后才能写金额、奖金、赔率、返点。
7. **SEO必须增加信息价值**：不通过同义改写、抓取拼接、关键词变体批量制造页面。
8. **生产隔离**：本仓库 → Approved Package → `fdsasaaa/xyptdq` → 迅睿CMS草稿 → `www.laocaimi.org`。

## 首批 时时彩 mechanics

当前 verified mechanics 覆盖：

- 一星直选 / 个位定位胆
- 后二直选
- 后三直选
- 五星直选
- 后二组选
- 后三组选3 / 组三
- 后三组选6 / 组六
- 单位置定位胆
- 后二大小单双

规则目录：`rules/mechanics/ssc/`

数学与判定实现：

- `engine/betmath.py`：直选笛卡尔积、组选组合数、理论直选覆盖率
- `engine/mechanics.py`：直选、后二组选、组三、组六、定位胆、大小单双判定
- `docs/SSC_HISTORICAL_MECHANICS_BASELINE.md`：来源、退市状态和应用边界

## 快速开始

```bash
python -m engine.cli init
python -m engine.cli status
python -m engine.cli audit
python -m engine.cli capability --provider <provider_id> --lottery 时时彩 --play 组三
python -m engine.cli plan --provider <provider_id> --lottery 时时彩 --play 组三 --count 10
```

规划结果有三档：

- `blocked_mechanics_verification`：玩法机制未核验，只能保留选题想法。
- `ready_mechanics_only`：可写玩法、选号、注数和中奖条件案例，但不能陈述未核验的金额/奖金/返点。
- `ready_full`：玩法机制和具体平台经济参数都已核验，可以生成完整案例。

## Provider 映射

- `schemas/provider_lottery_mapping.schema.json`：彩种/玩法映射数据协议
- `mappings/PROVIDER_MAPPING_POLICY.md`：分分彩、哈希分分彩等继承 mechanics 前的强制核验条件

即使 mapping 为 verified，经济参数仍不得从历史时时彩继承。

## 知识层

- `knowledge/source_sets/`：2406个精选来源ID
- `knowledge/family_archives/brbcw_families_v1.part-*.b64`：759个方法家族紧凑知识档案
- `knowledge/coverage/brbcw.json`：整体覆盖统计
- `knowledge/coverage/brbcw_report.md`：人类可读审计报告
- `knowledge/TECHNIQUE_TAXONOMY.json`：技巧原子词典

Git默认不保存2406篇论坛全文。需要回看案例时按来源ID定位原公开帖子。

## 规则层

- `schemas/mechanics_rule.schema.json`：玩法机制规则
- `schemas/economics_rule.schema.json`：平台经济规则
- `rules/PROVIDER_RULE_POLICY.md`：规则来源与核验政策
- `registry/rule_gaps.jsonl`：未来发现的规则缺口

## 发布层

- 网站仓库：`fdsasaaa/xyptdq`
- CMS：迅睿CMS
- `schemas/publish_package.schema.json`：内容引擎交付协议
- `publishing/XYPTDQ_BRIDGE.md`：草稿发布边界与验收规则

发布后必须把最终URL、发布日期、最终标题、技巧组合和内容指纹回写 `registry/articles.jsonl`，永久参与后续去重。

## 测试

```bash
pytest -q
python -m engine.cli audit
```
