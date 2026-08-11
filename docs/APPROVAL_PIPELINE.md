# Approval Pipeline

任何AI生成的正文都不能直接进入网站仓库。唯一正式路径：

`Draft Packet + Draft Article → Draft Review → Quality/Dedup → SEO Contract → Bet Compliance → Approved Package`

## 1. 自身生命周期不是重复内容

一篇文章会经历：

`idea → draft → approved → queued → published`

同一 `article_id` 的后续状态是同一篇文章的生命周期更新，不应被去重器当成另一篇重复文章。

`engine/dedup.py` 因此会跳过相同 `article_id`，但仍检查其他文章的 fingerprint 和核心内容重叠。

## 2. Registry 为 append-only，读取为 last-write-wins

`registry/articles.jsonl` 保留历史记录，不覆盖旧行。

但 `iter_registry("articles")` 返回同一 `article_id` 的最后有效记录。因此：

- idea 可以升级到 approved；
- published 可以成为最终有效状态；
- fingerprint / angle_signature / technique_atoms 等身份字段通过合并状态更新持续保留；
- SQLite rebuild 只索引每篇文章的当前有效状态。

## 3. Approval Gate

`engine/approval.py` 同时执行：

- `review_draft()`：Draft Packet合同、演示案例标签、保证性词汇、不可篡改 rule_refs；
- `quality.evaluate()`：规则能力、内容长度、重复风险、投注合规等；
- SEO contract：primary keyword、search intent、meta description、slug；
- 只有全部通过才创建 `status=approved` 的 Publish Package。

任何错误都返回：

`rejected_for_revision`

并且 `publish_package = null`。

## 4. Approved Package

Approved Package 遵守：

`schemas/publish_package.schema.json`

并附带：

- content_hash；
- fingerprint；
- provider / lottery / play；
- technique_atoms；
- approved_at。

它是内容引擎交给 `fdsasaaa/xyptdq` 的唯一允许输入。

## 5. CLI

只审核，不写Registry：

```bash
python -m engine.cli approve-draft \
  --packet packet.json \
  --article article.json \
  --output approved.json
```

审核并写回生命周期状态：

```bash
python -m engine.cli approve-draft \
  --packet packet.json \
  --article article.json \
  --output approved.json \
  --record
```

若审核失败，不生成 Approved Package，返回非零退出码。
