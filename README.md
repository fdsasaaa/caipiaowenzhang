# 老财迷彩票内容引擎（caipiaowenzhang）

这是 `laocaimi.org` 的独立内容研发仓库。它负责 Research/Content，不直接承担生产网站运行。

## 当前版本

`v0.2.0-knowledge-ingestion`

当前已接入首批 **2406篇 brbcw 精选来源**。它们被转成长期可维护的知识记忆，而不是把论坛全文直接塞进Git：

- 2406 个精选来源ID，可重建原始公开URL
- 2294 篇能识别出明确技巧原子
- 759 个方法家族，作为未来文章规划的经验层
- 1389 个精细方法簇已在抽取审计中统计
- 1321 篇带盈利、百分比或保证性等风险声明，统一隔离为来源声称
- Google SEO 官方政策快照与内容质量门禁
- `provider_id + 彩种 + 玩法` 三重规则门禁

## 核心原则

1. **规则先于文案**：玩法、注数、中奖条件、赔率/奖金、返点等必须绑定具体 `provider_id + lottery + play` 并核验。
2. **来源文章不是事实库**：论坛/历史文章中的命中率、稳赚、倍投收益只作为 `unverified_source`。
3. **禁止换皮重复**：标题不同但技巧原子、案例结构、搜索意图高度重合，也视为重复。
4. **案例必须可复算**：没有 verified rule 时，只能提出文章角度，不得输出确定性投注成本、奖金或合法性结论。
5. **SEO必须增加信息价值**：不通过同义改写、抓取拼接、关键词变体批量制造页面。
6. **生产隔离**：本仓库 → Approved Draft → 网站仓库 → WordPress/发布器 → `laocaimi.org`。

## 快速开始

```bash
python -m engine.cli init
python -m engine.cli status
python -m engine.cli audit
```

查看某个平台/彩种/玩法的候选文章角度：

```bash
python -m engine.cli plan --provider <provider_id> --lottery 时时彩 --play 定位胆 --count 10
```

如果没有对应 verified rule，规划器会返回 `blocked_rule_verification`。这是设计行为，不是报错。

## 知识层

- `knowledge/source_sets/`：2406个精选来源ID
- `knowledge/family_archives/brbcw_families_v1.bz2.b64`：759个方法家族的紧凑知识档案
- `knowledge/coverage/brbcw.json`：2406篇来源的整体覆盖统计
- `knowledge/coverage/brbcw_report.md`：人类可读审计报告
- `knowledge/TECHNIQUE_TAXONOMY.json`：技巧原子词典
- `scripts/extract_technique_candidates.py`：从受控原始资料重建候选/精细方法簇的工具

Git默认不保存2406篇论坛全文。方法家族保留技巧原子、位置、彩种、来源分类、来源支持数、风险声明率和代表来源ID；需要回看案例时，再按来源ID定位原公开帖子。

## 规则层

- `rules/PROVIDER_RULE_POLICY.md`：平台感知规则政策
- `schemas/rule.schema.json`：规则数据协议
- `rules/**/*.json`：具体已核验或待核验规则

> 同名彩种在不同平台上的单注金额、奖金/赔率、返点和限额可能不同。系统禁止把“通用印象”当平台规则。

## SEO层

- `seo/seo_profile.toml`：`laocaimi.org` 内容SEO配置
- `seo/google_policy_snapshot.toml`：Google官方政策快照

## 文章生命周期

`idea → draft → validated → approved → queued → published → monitored`

发布后必须写入 `registry/articles.jsonl`，永久参与后续去重。

## 测试

```bash
pytest -q
python -m engine.cli audit
```
