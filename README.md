# 老财迷彩票内容引擎（caipiaowenzhang）

`caipiaowenzhang` 是 `www.laocaimi.org` 的独立内容研发、生成与审核引擎。生产网站与最终发布仍由 `fdsasaaa/xyptdq` 承担。

## 当前版本

**v2.2.0**

V2 的目标是把“AI辅助写文章”升级成可持续的自动内容生产系统：新来源可以自动知识化并反哺选题，系统先排序候选，再调用受约束模型写正文，最后通过证据、规则、去重、SEO和投注合规门禁才产生 Approved Package。

V2.1 在此基础上新增**实操/编辑质量门禁**：程序不再把“所有硬规则通过”误当成“文章已经满分”。新文章除了 `quality_score`，还必须独立通过 `editorial_score`，证明读者能看懂实际操作步骤、候选空间如何变化、参数何时冻结，以及没有第二条已验证规则时何时停止继续加条件。

V2.2 再增加**多层筛选合同与机器候选空间引擎**：多层文章中的每个过滤器必须在查看演示样本前冻结，`before → after → excluded` 由 Python 穷举而不是交给模型心算；pipeline 数学 evidence 由系统确定性生成，模型只负责解释。V2.2 已完成真实 `gpt-5.4-mini` 五篇批次压力测试与针对唯一失败案例004的最小真实复验，最终 targeted confirmation 为 `generated=1 / approved=1`，hard/editorial/multistage 均为 `100`，因此版本正式晋升为 `2.2.0`。

## V2.2 主流水线

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
Draft Packet + Editorial Practicality Contract
  ↓ optional Multi-stage Filter Contract
机器穷举 before / after / excluded
  ↓ OpenAI Responses strict structured output
V2 AI Draft + claim_evidence + practical_guidance
  ↓
系统规范化 pipeline evidence / 演示披露
  ↓
Draft Review
  ↓
Claim → Evidence Gate
  ↓
Hard Quality + Editorial Quality + Multi-stage Quality + Rule + Bet Compliance + Structural Dedup + SEO Ownership
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

`engine/ai_generation.py` / `engine/ai_generation_v22.py` 使用 OpenAI Responses API structured outputs：

- API key只从环境变量 `OPENAI_API_KEY` 读取；
- `store=false`；
- strict JSON Schema；
- 模型不能修改article_id、主关键词、search intent、网站分类、rule/source refs、case scope；
- failed/incomplete/cancelled/refusal均fail-closed；
- 普通CI使用fake transport或纯离线测试，不调用真实外部API；
- 真实模型测试只能通过显式、临时、可拆除的执行路径进行。

### 5. V2.1 Editorial / Practical Quality

新 Blueprint 默认带 `editorial_contract_version`。已经存在于 Registry 的旧文章继续沿用原生命周期，不会被强制升级。

V2.1+ 新文章必须输出 `practical_guidance`：

- `steps`：至少4个具体操作步骤；
- `starting_space`：筛选前候选空间；
- `after_primary_filter_space`：筛选后候选空间；
- `parameter_freeze_rule`：参数必须先固定再看样本；
- `stop_condition`：没有额外已验证规则时必须明确停止；
- `next_step_policy`：只有新增条件有已验证规则/证据并能复算，才允许继续压缩候选。

审批结果同时返回：

- `quality_score`：硬质量、规则、重复与合规；
- `editorial_score`：读者可操作性与实用表达质量。

V2.1 的目标不是鼓励把更多条件拼在一起，而是强制文章说明“当前方法实际筛掉了什么、做到哪一步应该停”。

### 6. V2.2 Multi-stage Filter Contract

V2.2 允许文章使用多个**预冻结且可机器复算**的过滤阶段，但不允许模型临时发明第二、第三层技巧。

- `filter_pipeline_spec` 在查看演示数据前冻结；
- `engine/filter_pipeline.py` 枚举理论候选空间；
- 每层必须给出 `before_space / after_space / excluded_space`；
- 每层必须真实缩小候选空间；
- `experimental_parameter` 只能表示研究参数，不表示预测优势；
- pipeline 数学与 digit pool 参数基数属于系统自有 evidence；
- 模型把 pipeline calculation 错标为 synthetic case 时，只有与机器结果精确匹配的关系才允许规范化；
- 演示开奖号、样本和值/跨度/频率等仍必须严格使用 `synthetic_case`；
- `multistage_score` 独立于 hard/editorial score；
- 真实验收记录保存在 `agent/results/V22_LIVE_BATCH_STRESS_2026-08-12.md`。

当前正式 V2.2 的真实确认覆盖了固定五篇多层 benchmark，以及最终004后二组选复式 `45 → 10 → 7` targeted smoke。它验证的是生成/审核链路，不证明任何筛选方法具有预测优势或盈利能力。

### 7. Claim → Evidence

V2自动文章必须携带 `claim_evidence`。

- `verified_rule` 只能引用Draft Packet的rule refs；
- `source_unverified` 只能引用source refs，并明确标注“来源声称/未验证”；
- `synthetic_case` 只能引用case bundle；
- mechanics-only不能借claim evidence绕过economics门禁；
- 百分比、注数、命中率、赔率、返点、奖金、盈利、明确未来预测等硬声明没有证据登记就不能批准；
- 明确的风险否定句不会被误判成正向命中率/预测声明，但真正的正向表现声明仍必须有证据。

### 8. 双层去重

- 旧 lexical/core Jaccard 保留；
- exact fingerprint保留；
- 新增结构性方法去重：subject lottery、play family、technique atoms、case selector、case metrics、content type；
- Blueprint阶段先阻断，避免浪费模型调用；
- Approval再次阻断，防止外部AI或手工绕过。

### 9. SEO Topic Priority

没有真实外部数据时：

`signal_mode=internal_only`

按规则就绪度、source support、source risk、information gain、关键词归属和新颖性排序。

有真实Search Console/搜索需求信号时：

`signal_mode=external_augmented`

可加入 impressions、clicks、position，以及可选search volume。仓库不伪造任何搜索量。

`normalize_search_console_csv.py` 支持把常见中英文GSC查询报表CSV转换为标准signals JSONL。

### 10. 永久记忆与网站桥梁

- Registry append-only + last-write-wins；
- exact primary keyword唯一owner；
- Internal Link Planner只规划article_id关系，未发布URL保持null；
- 真实Publication Receipt出现后才写published_url；
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

V2.2 的 `fully_live_accepted` 表示多层文章链已经完成真实模型验收。它**仍不等于**以下外部条件自动成立：

1. 任意目标彩票平台的mechanics/economics都已经核验；
2. Search Console真实查询数据已经导入；
3. 某个筛选参数具有预测优势、命中率优势或盈利能力；
4. 网站文章发布冻结已经解除。

这些状态必须分开报告，不能用一个“100%”掩盖。

## 当前内容状态

现有8篇烟测文章仍保持已批准 + 网站draft-only。V2.2升级不会自动把它们promote、scheduled或published。

V2.1/V2.2 质量样本与真实API验收样本只用于文章系统验证；本轮V2.2真实测试始终 `Registry write=false / Website draft write=false / Scheduled=false / Published=false`。

## 关键文档

- `docs/SOURCE_INTELLIGENCE_V2.md`
- `docs/AUTO_GENERATION_V2.md`
- `docs/SEO_PRIORITY_V2.md`
- `docs/EDITORIAL_QUALITY_V21.md`
- `docs/CONTENT_LIFECYCLE_V1.md`
- `agent/results/V22_LIVE_BATCH_STRESS_2026-08-12.md`
- `publishing/XYPTDQ_BRIDGE.md`
