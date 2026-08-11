# Automatic Article Generation v2

V2 把旧流程中的“Draft Packet 后由人工调用AI”替换成正式的可审计执行层。

## 流程

```text
Blueprint
  ↓ lexical + structural dedup
Draft Packet
  ↓ OpenAI Responses structured-output executor
V2 Draft + claim_evidence
  ↓ Draft Review
Claim → Evidence Gate
  ↓ Quality + betting compliance
Structural duplicate gate
  ↓ SEO ownership
Approval
  ↓ only when all pass
Approved Package
```

模型永远没有直接批准、排期或发布权限。

## 模型执行

`engine/ai_generation.py` 默认使用 OpenAI Responses API，但 transport 是可注入的，因此 CI 不调用真实外部API。

运行时：

- API key 只读取 `OPENAI_API_KEY`；
- 模型可用 `OPENAI_MODEL` 或 `--model` 指定；
- 请求 `store=false`；
- 使用 `text.format.type=json_schema` + strict Structured Outputs；
- 输入只使用冻结 Draft Packet，不允许模型自行抓取来源网页或补充未提供事实；
- 输出必须保持 article_id、primary_keyword、search_intent、site_category_key、content_type、content_format、rule_refs、source_refs、case_scope 不变。

## Claim → Evidence

V2 自动生成文章必须返回 `claim_evidence`。

支持类型：

- `verified_rule`：只能引用 Draft Packet `rule_refs`；
- `synthetic_case`：只能引用 `case_bundle`；
- `source_unverified`：只能引用 `source_refs`，且 claim 文本必须明确写“来源声称/原文提到/未验证”等限定；
- `editorial`：不携带事实引用。

正文中出现百分比、命中率、准确率、注数、赔率、返点、奖金、盈利或明确未来预测等硬声明时，必须能在 `claim_evidence` 找到对应项。

`mechanics_only` 文章不能通过 claim_evidence 绕过 economics 门禁。

## 结构性去重

旧词法 Jaccard 继续保留。新增 `engine/semantic_dedup.py`，用确定性技术结构打分：

- subject lottery；
- play family；
- technique atoms；
- case selector；
- case metrics；
- content type。

因此即使标题、SEO关键词和示例号码全部更换，只要文章仍是同一个玩法+技巧+案例结构，也会被识别为 method-level overlap。

该门禁同时用于：

1. Blueprint 阶段——正文生成前阻断，节省模型调用；
2. Quality/Approval 阶段——防止手工或外部AI绕过 Blueprint。

## 一键生成+审核

```bash
OPENAI_API_KEY=... \
python scripts/generate_and_review_v2.py \
  --packet packet.json \
  --draft-output draft.json \
  --report-output review.json \
  --approved-output approved.json
```

默认不写 Registry。

只有明确需要把审核状态写入生命周期时才添加：

```bash
--record
```

模型调用成功并不等于审批成功。无论模型输出是否完整，只要 Claim/Evidence、质量、规则、投注合规、结构去重或SEO任一门禁失败，`approved.json` 都不会生成。

## 发布边界

V2 自动生成层只负责 Draft/Approved Package，不自动 promote、不写 `content/scheduled`、不调用网站 Native Publisher。
