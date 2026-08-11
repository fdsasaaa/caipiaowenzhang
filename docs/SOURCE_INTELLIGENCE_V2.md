# Source Intelligence v2

目标：把未来持续采集的原始文章转换成可审计的知识卡，而不是把原文直接交给AI自由改写。

## 输入

支持 JSON 或 JSONL。正文可使用 `cleaned_content / content_text / content / body / text` 任一字段。

## 流程

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

## 命令

```bash
python scripts/ingest_sources_v2.py input.jsonl \
  --output knowledge/incoming/cards.jsonl \
  --quarantine knowledge/incoming/quarantine.jsonl
```

## 数据边界

Knowledge Card 默认不保存整篇原文，只保存结构化知识、hash、风险声明及短 evidence snippets。原始材料可以继续保存在独立采集存储中。
