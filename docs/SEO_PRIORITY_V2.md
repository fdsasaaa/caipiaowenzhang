# SEO Topic Priority v2

目标：在调用模型前先回答“下一批最值得写什么”，而不是只回答“哪些主题能写”。

## 排序原则

### Internal evidence

任何时候都可用：

- Blueprint 必须 `ready_for_draft`；
- verified mechanics + case ready；
- source support count；
- source risk rate；
- explicit information gain；
- exact primary keyword 未被占用；
- lexical + structural novelty gates 均通过。

被 keyword / duplicate / mechanics / case semantics 阻断的 Blueprint 即使外部搜索量很高，也保持 `eligible=false`。

### External demand signals（可选）

可接受标准化字段：

- `primary_keyword` / `query` / `keyword`；
- `impressions`；
- `clicks`；
- `position`；
- 可选 `search_volume`；
- 可选 `competition`；
- `source` 必填，例如 `google_search_console`。

当前仓库没有伪造任何 Search Console 数据。

没有 signals 时：

```text
signal_mode = internal_only
```

有真实数据输入时：

```text
signal_mode = external_augmented
```

这样内部知识支持度不会被包装成“搜索量”。

## Opportunity logic

外部信号主要用于发现：

- 有 impressions、排名约4-20位的提升机会；
- 排名20-50位但已经有可见需求的中尾部机会；
- impressions 已有但 CTR 偏低的标题/意图机会；
- 可选第三方 search-volume 信号。

外部信号只加权“已经合规、独特、规则就绪”的候选主题，不解除任何生成门禁。

## 命令

内部证据排序：

```bash
python scripts/rank_topics_v2.py \
  --provider historical_official \
  --lottery 时时彩 \
  --play 后三直选 \
  --count 20
```

加入标准化需求信号：

```bash
python scripts/rank_topics_v2.py \
  --provider historical_official \
  --lottery 时时彩 \
  --play 后三直选 \
  --count 20 \
  --signals seo/signals/search_console.jsonl \
  --output rankings/housan.json
```

## 数据合同

见 `schemas/seo_demand_signal.schema.json`。

本层只排序选题，不修改 Registry，不生成文章，不进入 website draft/scheduled。
