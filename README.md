# 老财迷彩票内容引擎（caipiaowenzhang）

`caipiaowenzhang` 是 `www.laocaimi.org` 的独立内容研发与审核引擎。它负责知识、规则、研究、文章规划、AI写作约束、去重和批准；生产网站与最终发布由 `fdsasaaa/xyptdq` 承担。

## 当前版本

`v1.0.0-site-contract`

## v1.0 的关键变化

内容引擎与网站仓库现在使用明确的跨仓库合同：

- 当前“投注技巧文章”统一标记 `content_type=technique_article`；
- 内容引擎明确分配 `site_category_key=tzjq`；
- AI正文必须输出 `content_format=html`；
- Draft Packet 冻结 content_type / site_category_key / content_format；
- Draft Review 禁止AI改分类、改格式或插入 script/iframe/form/object/embed；
- Approved Package 必须携带以上字段、fingerprint、content_hash；
- 网站侧只把 `site_category_key` 映射为数值 catid，不根据标题猜分类。

合同：`publishing/LAOCAIMI_SITE_CONTRACT.json`

当前注册内容类型：

- `technique_article → tzjq`
- `hangup_scheme → gjfa`
- `resource_article → zyyy`
- `seo_topic → seo-articles`

当前文章生成器只默认生成 `technique_article`。其他类型必须由对应生成器显式声明，未知类型 fail-closed。

## 当前正式能力

- 2406 个 brbcw 精选来源ID；2294篇可识别技巧原子；759个方法家族、1389个精细方法簇。
- mechanics / economics 双层规则；未核验奖金、赔率、返点、限额不得当事实。
- 时时彩历史机制基线及位置同构规则；分分彩等必须显式 provider mapping。
- 和值、跨度、频率、遗漏、奇偶、大小、重号、邻号等可执行指标与可复算案例。
- Article Blueprint：正文生成前固定搜索意图、技巧原子、SEO字段、案例算法、fingerprint和网站分类。
- 永久角度记忆：`idea / draft / approved / queued / published` 全生命周期参与去重。
- Draft Packet：冻结规则、来源、SEO、案例、HTML格式、网站分类和禁止表述后再交给AI。
- Approval Pipeline：Draft Review + Quality/Dedup + SEO Contract + Bet Compliance 全通过后才产生 Approved Package。
- 用户内部 90%金额 + 90%目标空间覆盖门禁；支持跨玩法并集与高级倍投阶段检查。
- 定码轮换三级玩法格式Registry与可执行语法校验。
- 防过拟合、随机基准、样本外和失败实验记录研究协议。

## 主流水线

```text
来源资料
  ↓
技巧原子 / 方法家族
  ↓
玩法规则校验
  ↓
Article Blueprint + site_category_key
  ↓
预写作查重 + reserve idea
  ↓
Draft Packet（HTML + 网站分类冻结）
  ↓
AI Draft
  ↓
Draft Review
  ↓
Quality + Dedup + SEO + Bet Compliance
  ↓
Approved Package
  ↓
fdsasaaa/xyptdq
  ↓
content/drafts
  ↓ 显式晋级
content/scheduled
  ↓
已验证 Native Publisher
  ↓
迅睿CMS
  ↓
最终URL/状态回写Registry
```

## 不可绕过的边界

1. **规则先于文案**：mechanics 未核验不能写确定性玩法案例；economics 未核验不能写平台金额、奖金、返点、限额事实。
2. **内部策略与平台事实分开**：90%金额/覆盖是用户内部硬门禁，不宣称为平台官方规定。
3. **统计不是预测保证**：冷热是窗口频率，遗漏是等待距离；历史结构不自动意味着下一期更容易发生。
4. **来源不是事实库**：论坛命中率、稳赚、盈利说法仅作为未验证来源声称。
5. **禁止换皮重复**：核心方法只换标题、号码或同义词仍视为重复。
6. **网站分类由内容引擎明确决定**：网站侧不能猜 category。
7. **正文格式是HTML合同**：AI不能输出纯Markdown后仍通过批准。
8. **违规投注案例不能批准**：金额、覆盖、跨玩法或高级倍投门禁失败，Approved Package 不生成。
9. **生产隔离**：内容引擎不直接修改生产服务器数据库。

## Registry 生命周期

`registry/articles.jsonl` 是 append-only 历史日志。同一 `article_id` 可依次：

`idea → draft → approved → queued → published`

有效读取采用 last-write-wins；状态更新保留 fingerprint、angle_signature、technique_atoms、content_type、site_category_key、content_format 等身份字段。去重器忽略文章自己的生命周期记录，但继续与其他文章比较。

## 文章生成与审核 CLI

```bash
python -m engine.cli audit

python -m engine.cli blueprints \
  --provider <provider_id> --lottery 时时彩 --play 后三直选 --count 10 --reserve

python -m engine.cli draft-packets \
  --provider <provider_id> --lottery 时时彩 --play 后三直选 --count 10

python -m engine.cli approve-draft \
  --packet packet.json \
  --article article.json \
  --output approved.json \
  --record
```

## 投注组合硬门禁

配置：`policies/BET_COMPLIANCE_POLICY.json`

实现：`engine/compliance.py`

- 同一期 + 同彩种 + 同目标中奖空间联合校验；
- 跨玩法先映射 `target_space_id + covered_outcomes`；
- 覆盖集合去重求并集；
- 覆盖率 >90% 阻断；
- 金额 >参考奖金90% 阻断；
- `phase_amounts` 对高级倍投各阶段汇总；
- 缺目标空间映射时 fail-closed；
- 违规时禁止导出。

## 定码轮换与研究层

- `formats/dingma_rotation_v1.json`
- `formats/dingma_rotation_counts_v1.json`
- `engine/format_rules.py`
- `knowledge/research/USER_RESEARCH_TAXONOMY_V1.json`
- `engine/analysis_metrics.py`
- `engine/casebook.py`
- `knowledge/TECHNIQUE_SEMANTICS.json`

平台行为未确认的四星/五星组选、任选、和值、龙虎等继续保持 pending。研究优先级强调数据质量、规则版本、理论概率、随机基准、样本外、walk-forward、多重检验和失败记录。

## 关键协议

- `publishing/LAOCAIMI_SITE_CONTRACT.json` — 内容类型/网站分类/HTML合同
- `docs/ARTICLE_GENERATION_PIPELINE.md`
- `docs/ARTICLE_CASE_STANDARD.md`
- `docs/DRAFT_PACKET_STANDARD.md`
- `docs/APPROVAL_PIPELINE.md`
- `docs/USER_RULES_INGEST_2026-08-11.md`
- `schemas/article_blueprint.schema.json`
- `schemas/draft_packet.schema.json`
- `schemas/publish_package.schema.json`
- `publishing/XYPTDQ_BRIDGE.md`

## 测试

```bash
pytest -q
python -m engine.cli audit
```

正式变更继续通过独立分支、PR与 GitHub Actions 后进入 `main`。
