# Source Intelligence v2

目标：把未来持续采集的原始文章转换成可审计的知识卡，并自动反哺 Planner，而不是把原文直接交给AI自由改写。

## 输入

支持 JSON 或 JSONL。正文可使用 `cleaned_content / content_text / content / body / text` 任一字段。

## 完整流程

```text
raw source
  ↓ normalize
quality assessment
  ↓
keep / quarantine / reject
  ↓ keep only
lottery / position / topic detection
  ↓
technique atoms
  ↓
case features
  ↓
source claims + exact evidence snippets
  ↓
Source Knowledge Card v2
  ↓ aggregate by technique atoms
Dynamic Technique Families v2
  ↓
Planner static families + dynamic families
  ↓
Blueprint / SEO Priority / Draft Packet
```

## 质量分流

当前硬信号包括：

- 空正文；
- 极短正文；
- Discuz printable/generic title；
- 常见回复灌水；
- 广告/联系方式；
- header-only正文；
- exact content duplicate。

低质量来源不会进入正常知识池；`quarantine/reject` 可单独保存，便于人工复查而不是永久丢失。

## 技巧知识

继续复用 `knowledge/TECHNIQUE_TAXONOMY.json`，自动抽取：

- lottery terms；
- positions/windows；
- canonical technique atoms；
- topic tags；
- history-window / example / previous-draw 等案例特征。

所有来源技巧默认仍是 `unverified_source`，`publishable=false`，必须通过 verified mechanics/rules 才能进入确定性教程。

## Claim → Evidence source layer

来源中出现：

- 百分比准确率/命中率；
- 盈利/收益；
- 必中/稳赚/保证；
- 明确未来预测；

会被拆成独立 claim，并保留：

- source_id；
- 字符起止位置；
- 原句短证据；
- evidence snippet SHA-256；
- claim type；
- risk score；
- `unverified_source_claim` 状态。

这只是来源证据索引，不代表该声明成立。

## Dynamic Technique Families v2

`engine/knowledge_families_v2.py` 会把 eligible knowledge cards 按 technique atoms 聚合成动态方法家族，并计算：

- source_count；
- risk_rate；
- lotteries；
- positions；
- source classifications；
- representative source IDs；
- `origin=dynamic_source_intelligence_v2`。

Planner 会同时读取：

1. 既有 brbcw static/compact family knowledge；
2. `knowledge/dynamic_families/*.jsonl`。

因此以后新增来源不需要重新生成原来的 compact brbcw archive。动态来源只有在玩法规则、selector 和 case semantics 同样通过时才会成为可生成文章。

## 一步摄取并接入 Planner

```bash
python scripts/ingest_sources_v2.py input.jsonl \
  --output knowledge/incoming/cards.jsonl \
  --quarantine knowledge/incoming/quarantine.jsonl \
  --families-output knowledge/dynamic_families/incoming.jsonl
```

不指定 `--families-output` 时只生成知识卡，不改变 Planner 的动态知识输入。

## 数据边界

Knowledge Card 默认不保存整篇原文，只保存结构化知识、hash、风险声明及短 evidence snippets。原始材料可以继续保存在独立采集存储中。

Dynamic Family 也不保存整篇原文，只保存聚合后的方法结构和代表 source IDs。
