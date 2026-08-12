# 文章生产总控（Article Production Controller）

## 目标

把“帮我生成 200 篇 / 500 篇正式文章”变成系统级任务，而不是一次性让模型硬写指定数量。

总控把用户给出的数量视为 **Approved 正式文章目标**。它不能为了凑数降低规则、证据、SEO、去重、编辑质量或合规标准。

## 数量政策

机器政策：`policies/ARTICLE_PRODUCTION_CONTROLLER.json`

建议使用：

- 1–49：允许，适合专题或实验；
- 50–300：推荐日常范围；
- 200：默认目标；
- 301–500：普通大型扩库任务；
- 501–2000：大型任务，必须先做容量预检；
- 2000 以上：超大型任务，需要显式 ultra opt-in，而且容量预检仍然必须证明当前知识空间足够。

内部实际执行默认 **25 篇/批**，正常允许 20–30 篇。目标 500 篇并不意味着一次请求 500 篇，而是类似 25 × 20 个内部批次，并持续使用已经完成的 Registry / Approved 库存重新阻止重复主题。

## 核心流程

```text
用户目标数量
  ↓
读取已验证 mechanics + 当前知识家族
  ↓
内容空间容量预检
  ↓
生成候选 Blueprint
  ↓
公开主题映射（当前 时时彩 mechanics 默认面向读者使用 分分分彩/分分彩 体系中的“分分彩”）
  ↓
全库 article_id / Primary Keyword / 结构签名去重
  ↓
SEO Priority 排序
  ↓
约 25 篇内部批次
  ↓
AI Draft
  ↓
正常 Approval Pipeline
  ↓
读者术语审计
  ↓
正式 Approved Package 入库 articles/approved/
  ↓
达到目标，或当前可执行内容空间/质量空间耗尽即停止
```

## 容量优先于凑数

总控首先从仓库中已验证 mechanics 自动发现可执行的 `lottery + play` 工作单元，再读取 Planner 的真实知识家族生成候选。

容量估算不是“理论上 AI 能写多少段文字”，而是当前仓库在以下门禁之后还剩多少不同候选：

- mechanics 已验证；
- Case Engine 可执行；
- Primary Keyword 未被占用；
- Registry 没有已有 angle；
- 正式 Approved 库存没有同 article_id；
- 正式 Approved 库存没有同 Primary Keyword；
- 结构签名不重复；
- SEO Priority eligible。

如果用户要求 500 篇，而当前安全候选只有 327 篇，总控应把 327 作为当前容量事实，不得自动放宽门槛创造剩余 173 篇。

## FFC 公开语义

当前已验证玩法 mechanics 可能仍使用历史/internal `时时彩` taxonomy。总控默认通过机器政策把这种内部规则主题映射为读者侧 `分分彩`，但：

- 不篡改 rule_refs；
- 不篡改来源 provenance；
- 不把历史规则名伪造为新的规则；
- 正式入库前仍运行 reader terminology audit；
- FFC 正式文章默认获得 `primary_seo_cluster_id=ffc_research`，该字段来自总控政策而不是正文模型猜测。

以后 Hash FFC、奇趣分分彩、赛车/飞艇等只有在对应规则/知识合同真实准备好后才能加入总控工作空间，不能仅靠改标题扩充数量。

## 安全门

总控 **没有** 以下权限：

- 同步网站；
- 创建网站 Draft；
- 创建 publish_at；
- 排期；
- 调用 Native Publisher；
- 修改 Publisher cron；
- 发布文章。

总控的终点只有：

`caipiaowenzhang/articles/approved/*.json`

网站 Approved → Draft、Scheduled、Published 仍属于其他独立门禁。

## 使用

### 只做容量预检，不调用模型

```bash
python scripts/produce_articles_total.py 200
```

默认只生成 `plan.json`，不会调用付费模型。

### 正式生产 200 篇

```bash
OPENAI_API_KEY=... \
python scripts/produce_articles_total.py 200 --execute
```

### 正式生产 500 篇

```bash
OPENAI_API_KEY=... \
python scripts/produce_articles_total.py 500 --execute
```

### 超过 2000 篇

必须显式：

```bash
python scripts/produce_articles_total.py 5000 --allow-ultra
```

即使显式允许，容量不足仍然不会进入“凑数模式”。

## 自然语言入口

ChatGPT / Agent 可以把以下用户表达解析为本总控任务：

- `启动文章生产总控，目标 200 篇正式文章。`
- `帮我生成 500 篇高质量文章。`
- `再补 100 篇正式文章。`

默认解释：

1. 数字指 **新增正式 Approved Package 目标**；
2. 先运行容量预检；
3. 分批执行；
4. 不合格不计数；
5. 合格文章进入 `articles/approved/`；
6. 不同步网站、不排期、不发布；
7. 如果当前知识空间不足，交付实际可安全完成数量和缺口，不降低门槛。

## 最终报告

正式执行结果至少报告：

- 目标数；
- 候选容量；
- 实际尝试数；
- 模型成功数；
- Approval 通过数；
- 正式入库数；
- Generation / Approval / terminology / inventory 失败数；
- Quality 与 Editorial 平均分；
- 玩法分布；
- SEO 主集群分布；
- 停止原因；
- 网站同步 / 排期 / 发布必须始终为 false。
