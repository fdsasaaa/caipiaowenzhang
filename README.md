# 老财迷彩票内容引擎（caipiaowenzhang）

`caipiaowenzhang` 是 `www.laocaimi.org` 的独立内容研发与审核引擎。它负责知识、规则、研究、文章规划、AI写作约束、去重和批准；生产网站运行由 `fdsasaaa/xyptdq` 承担。

## 当前版本

`v0.9.0-approval-pipeline`

## 当前正式能力

- 2406 个 brbcw 精选来源ID；2294篇可识别技巧原子；759个方法家族、1389个精细方法簇。
- 玩法机制 mechanics 与平台经济参数 economics 分层；未核验奖金、赔率、返点、限额不得当事实。
- 时时彩历史玩法机制基线及前/中/后位置同构规则；分分彩等必须显式 provider mapping。
- 和值、跨度、频率、遗漏、奇偶、大小、重号、邻号等可执行指标与可复算案例。
- Article Blueprint：正文生成前固定搜索意图、技巧原子、SEO字段、案例算法和 fingerprint。
- 永久角度记忆：`idea / draft / approved / queued / published` 全生命周期参与去重。
- Draft Packet：冻结规则、来源、SEO、案例和禁止表述后再交给AI写正文。
- Approval Pipeline：Draft Review + Quality/Dedup + SEO Contract + Bet Compliance 全部通过后才能生成 Approved Package。
- 用户内部 90%金额 + 90%目标空间覆盖硬门禁；支持跨玩法目标空间并集与高级倍投阶段检查。
- 定码轮换三级玩法格式Registry与可执行语法校验。
- 用户研究指标体系、防过拟合、随机基准和样本外验证协议。

## 主流水线

```text
来源资料
  ↓
技巧原子 / 方法家族
  ↓
玩法规则校验
  ↓
Article Blueprint
  ↓
预写作查重
  ↓
reserve idea
  ↓
Draft Packet
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
迅睿CMS草稿
  ↓
发布
  ↓
最终URL/状态回写Registry
```

## 不可绕过的边界

1. **规则先于文案**：mechanics 未核验不能写确定性玩法案例；economics 未核验不能写平台金额、奖金、返点、限额事实。
2. **用户策略与平台事实分开**：90%金额/覆盖阈值是内部硬门禁，不宣称为某个平台官方规定。
3. **统计不是预测保证**：冷热是窗口频率，遗漏是等待距离；历史结构不能自动推导下一期更容易发生。
4. **来源不是事实库**：论坛中的命中率、稳赚、盈利说法只保留为未验证来源声称。
5. **禁止换皮重复**：同一核心方法只换标题、数字或同义词仍视为重复。
6. **AI不能自由改事实**：Draft Packet 中的 rule_refs、玩法、案例边界和身份字段属于冻结输入。
7. **违规案例不能批准**：可执行投注案例若违反金额、覆盖、跨玩法或高级倍投门禁，不能进入 Approved Package。
8. **生产隔离**：内容引擎不直接修改生产服务器数据库。

## Registry 生命周期

`registry/articles.jsonl` 是 append-only 历史日志。

同一个 `article_id` 的状态可以依次更新：

`idea → draft → approved → queued → published`

读取时采用 **last-write-wins**，所以当前状态始终是最后一条记录；更新状态时保留原 fingerprint、angle_signature、technique_atoms 等身份信息。去重器会忽略同一个 `article_id` 自己，但继续与其他文章比较。

说明：`docs/APPROVAL_PIPELINE.md`

## 文章生成与审核 CLI

```bash
# 规则/仓库自检
python -m engine.cli audit

# 生成候选蓝图并永久占位
python -m engine.cli blueprints \
  --provider <provider_id> --lottery 时时彩 --play 后三直选 --count 10 --reserve

# 生成受约束的AI写作包
python -m engine.cli draft-packets \
  --provider <provider_id> --lottery 时时彩 --play 后三直选 --count 10

# 审核AI正文；通过才写 Approved Package
python -m engine.cli approve-draft \
  --packet packet.json \
  --article article.json \
  --output approved.json \
  --record
```

## 投注组合硬门禁

配置：`policies/BET_COMPLIANCE_POLICY.json`

实现：`engine/compliance.py`

标准化投注：`schemas/normalized_bet.schema.json`

核心逻辑：

- 同一期 + 同彩种 + 同目标中奖空间联合校验；
- 不同玩法先映射到 `target_space_id + covered_outcomes`；
- 覆盖集合去重后求并集；
- 覆盖率 > 90% 阻断；
- 同目标空间当期金额 > 参考奖金90% 阻断；
- `phase_amounts` 对高级倍投各阶段分别汇总；
- 缺少目标空间映射时 fail-closed；
- 违规时禁止导出。

跨玩法目标空间基础实现：`engine/target_spaces.py`。

## 定码轮换格式

- `formats/dingma_rotation_v1.json`
- `formats/dingma_rotation_counts_v1.json`
- `engine/format_rules.py`

已固定：直选单式/复式不同；五位置定位胆/单位置不同；和值多位数字保持原子；组选包胆不能按“输入一个数字=1注”理解。

平台行为未确认的四星/五星组选、任选、和值、龙虎等继续保持 pending，不能自动升级为 verified。

## 研究层

- `knowledge/research/USER_RESEARCH_TAXONOMY_V1.json`
- `engine/analysis_metrics.py`
- `engine/casebook.py`
- `knowledge/TECHNIQUE_SEMANTICS.json`

研究优先级强调：数据质量、规则版本、理论概率、随机基准、样本外、walk-forward、多重检验和失败记录。高阶机器学习/遗传搜索属于高过拟合风险；民间文化方法仅作为 research-only 题材。

## 关键协议与文档

- `docs/ARTICLE_GENERATION_PIPELINE.md` — 总文章生成流水线
- `docs/ARTICLE_CASE_STANDARD.md` — 案例标准
- `docs/DRAFT_PACKET_STANDARD.md` — AI写作冻结包
- `docs/APPROVAL_PIPELINE.md` — 正文批准与生命周期
- `docs/USER_RULES_INGEST_2026-08-11.md` — 用户规则摄取审计
- `schemas/article_blueprint.schema.json`
- `schemas/draft_packet.schema.json`
- `schemas/publish_package.schema.json`
- `publishing/XYPTDQ_BRIDGE.md`

## 测试

```bash
pytest -q
python -m engine.cli audit
```

所有正式变更通过独立分支、PR和 GitHub Actions 后再进入 `main`。
