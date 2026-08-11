# 老财迷彩票内容引擎（caipiaowenzhang）

`caipiaowenzhang` 是 `www.laocaimi.org` 的独立内容研发、生成与审核引擎。生产网站与最终发布仍由 `fdsasaaa/xyptdq` 承担。

## 当前版本

**v2.0.0**

V2 的目标是把“AI辅助写文章”升级成可持续的自动内容生产系统：新来源可以自动知识化并反哺选题，系统先排序候选，再调用受约束模型写正文，最后通过证据、规则、去重、SEO和投注合规门禁才产生 Approved Package。

## V2 主流水线

```text
新采集文章
  ↓ Source Intelligence v2
keep / quarantine / reject
  ↓
Source Knowledge Cards
  ↓ Dynamic Technique Families
Planner（旧2406来源 + 新动态知识）
  ↓
Blueprint
  ↓ exact keyword + lexical + structural dedup
SEO Topic Priority
  ↓
Draft Packet
  ↓ OpenAI Responses strict structured output
V2 AI Draft + claim_evidence
  ↓
Draft Review
  ↓
Claim → Evidence Gate
  ↓
Quality + Rule + Bet Compliance + Structural Dedup + SEO Ownership
  ↓
Approved Package
  ↓
fdsasaaa/xyptdq/content/drafts
```

**自动生成不等于自动发布。** Draft → Scheduled → Native Publisher 仍是网站仓库的独立显式生命周期，当前发布冻结边界继续有效。

## V2 核心能力

### 1. Source Intelligence v2

- JSON/JSONL通用来源入口，不再绑死brbcw；
- 自动识别空正文、短正文、Discuz打印页错解析、回复灌水、广告、header-only；
- exact正文重复隔离；
- 自动抽取彩种、位置、技巧原子、主题和案例特征；
- 百分比、盈利、必中、未来预测等拆为 `unverified_source_claim`，保留source/evidence位置和短证据hash；
- 默认知识卡不复制整篇来源正文。

### 2. Dynamic Technique Families

新知识卡可自动聚合成 `knowledge/dynamic_families/*.jsonl`，Planner同时读取：

- 既有2406精选来源形成的静态知识；
- 后续新采集文章形成的动态方法家族。

因此未来新增资料会真实改变候选方法与source support，不只是被存档。

### 3. 规则与案例

- mechanics / economics 分层；
- mechanics未核验不能写确定性玩法案例；
- economics未核验不能写具体平台奖金、赔率、返点、限额或收益事实；
- 和值、跨度、频率、遗漏、奇偶、大小、重号、邻号等已有可执行指标；
- synthetic case必须标记“演示数据，不是真实开奖记录”；
- 用户内部90%金额+90%覆盖门禁继续作用于可执行投注案例。

### 4. 自动模型写作

`engine/ai_generation.py` 使用 OpenAI Responses API structured outputs：

- API key只从环境变量 `OPENAI_API_KEY` 读取；
- `store=false`；
- strict JSON Schema；
- 模型不能修改article_id、主关键词、search intent、网站分类、rule/source refs、case scope；
- failed/incomplete/cancelled/refusal均fail-closed；
- CI使用fake transport，不调用真实外部API。

### 5. Claim → Evidence

V2自动文章必须携带 `claim_evidence`。

- `verified_rule` 只能引用Draft Packet的rule refs；
- `source_unverified` 只能引用source refs，并明确标注“来源声称/未验证”；
- `synthetic_case` 只能引用case bundle；
- mechanics-only不能借claim evidence绕过economics门禁；
- 百分比、注数、命中率、赔率、返点、奖金、盈利、明确未来预测等硬声明没有证据登记就不能批准。

### 6. 双层去重

- 旧 lexical/core Jaccard 保留；
- exact fingerprint保留；
- 新增结构性方法去重：subject lottery、play family、technique atoms、case selector、case metrics、content type；
- Blueprint阶段先阻断，避免浪费模型调用；
- Approval再次阻断，防止外部AI或手工绕过。

### 7. SEO Topic Priority

没有真实外部数据时：

`signal_mode=internal_only`

按规则就绪度、source support、source risk、information gain、关键词归属和新颖性排序。

有真实Search Console/搜索需求信号时：

`signal_mode=external_augmented`

可加入 impressions、clicks、position，以及可选search volume。仓库不伪造任何搜索量。

`normalize_search_console_csv.py` 支持把常见中英文GSC查询报表CSV转换为标准signals JSONL。

### 8. 永久记忆与网站桥梁

- Registry append-only + last-write-wins；
- exact primary keyword唯一owner；
- Internal Link Planner只规划article_id关系，未发布URL保持null；
-真实Publication Receipt出现后才写published_url；
- 内链插入产生新content hash，必须重新Approval。

## 常用命令

### 新来源 → 知识卡 → 动态方法家族

```bash
python scripts/ingest_sources_v2.py input.jsonl \
  --output knowledge/incoming/cards.jsonl \
  --quarantine knowledge/incoming/quarantine.jsonl \
  --families-output knowledge/dynamic_families/incoming.jsonl
```

### Search Console CSV标准化

```bash
python scripts/normalize_search_console_csv.py gsc.csv \
  --output seo/signals/search_console.jsonl
```

### 选题优先级

```bash
python scripts/rank_topics_v2.py \
  --provider <provider_id> \
  --lottery 时时彩 \
  --play 后三直选 \
  --count 20 \
  --signals seo/signals/search_console.jsonl
```

`--signals` 可省略；省略时明确使用internal-only排序。

### 单篇自动生成 + 审核

```bash
OPENAI_API_KEY=... \
python scripts/generate_and_review_v2.py \
  --packet packet.json \
  --draft-output draft.json \
  --report-output review.json \
  --approved-output approved.json
```

### 一批自动排序 + 生成 + 审核

```bash
OPENAI_API_KEY=... \
python scripts/produce_ranked_batch_v2.py \
  --provider <provider_id> \
  --lottery 时时彩 \
  --play 后三直选 \
  --count 5 \
  --output-dir runs/batch-001
```

同一批候选还会再做一次方法结构去重。默认不写Registry；只有明确需要生命周期记录时才加 `--record`。

### V2 readiness

```bash
python scripts/v2_readiness.py
```

也可以检查某个目标玩法与外部SEO信号：

```bash
python scripts/v2_readiness.py \
  --provider <provider_id> \
  --lottery 时时彩 \
  --play 后三直选 \
  --signals seo/signals/search_console.jsonl
```

## “V2完成”与外部依赖的区别

`v2_code_ready=true` 表示仓库已具备完整的文章创建代码链。

它**不等于**以下外部条件已自动成立：

1. `OPENAI_API_KEY` 已配置并完成真实模型调用；
2. Search Console真实查询数据已经导入；
3. 任意目标彩票平台的mechanics/economics都已经核验；
4. 网站文章发布冻结已经解除。

这些状态由 `v2_readiness.py` 分开报告，不能用一个“100%”掩盖。

## 当前内容状态

现有8篇烟测文章仍保持已批准 + 网站draft-only。V2升级不会自动把它们promote、scheduled或published。

## 关键文档

- `docs/SOURCE_INTELLIGENCE_V2.md`
- `docs/AUTO_GENERATION_V2.md`
- `docs/SEO_PRIORITY_V2.md`
- `docs/CONTENT_LIFECYCLE_V1.md`
- `publishing/XYPTDQ_BRIDGE.md`

## 测试

```bash
pytest -q
python -m engine.cli audit
python scripts/v2_readiness.py
```

正式变更继续通过独立分支、PR和GitHub Actions后进入`main`。
