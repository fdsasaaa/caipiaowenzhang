# 老财迷彩票内容引擎（caipiaowenzhang）

这是 `laocaimi.org` 的独立内容研发仓库。它负责 Research/Content，不直接承担生产网站运行。

## 当前版本

`v0.3.0-rule-layer`

当前基础资产：

- 2406 个 brbcw 精选来源ID，可重建原始公开URL
- 2294 篇能识别出明确技巧原子
- 759 个方法家族，作为未来文章规划经验层
- 1389 个精细方法簇已完成抽取审计
- 1321 篇带盈利、百分比或保证性风险声明，统一隔离为来源声称
- Google SEO 官方政策快照与内容质量门禁
- 玩法机制 / 平台经济参数 双层规则系统
- `caipiaowenzhang → fdsasaaa/xyptdq → www.laocaimi.org` 草稿发布协议

## 核心原则

1. **玩法机制与经济参数分开**：选号范围、投注格式、注数公式、中奖条件可以建立通用玩法规则；单注金额、奖金/赔率、返点、限额必须绑定具体平台。
2. **来源文章不是事实库**：论坛/历史文章中的命中率、稳赚、倍投收益只作为 `unverified_source`。
3. **禁止换皮重复**：标题不同但技巧原子、案例结构、搜索意图高度重合，也视为重复。
4. **案例必须可复算**：玩法机制未核验时只能提出选题；机制核验后可写规则案例；只有平台经济参数核验后才能写金额、奖金、赔率、返点。
5. **SEO必须增加信息价值**：不通过同义改写、抓取拼接、关键词变体批量制造页面。
6. **生产隔离**：本仓库 → Approved Package → `fdsasaaa/xyptdq` → 迅睿CMS草稿 → `www.laocaimi.org`。

## 快速开始

```bash
python -m engine.cli init
python -m engine.cli status
python -m engine.cli audit
python -m engine.cli capability --provider <provider_id> --lottery 时时彩 --play 定位胆
python -m engine.cli plan --provider <provider_id> --lottery 时时彩 --play 定位胆 --count 10
```

规划结果有三档：

- `blocked_mechanics_verification`：玩法机制未核验，只能保留选题想法。
- `ready_mechanics_only`：可写玩法、选号、注数和中奖条件案例，但不能陈述未核验的金额/奖金/返点。
- `ready_full`：玩法机制和具体平台经济参数都已核验，可以生成完整案例。

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
