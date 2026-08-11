# 老财迷彩票内容引擎（caipiaowenzhang）

这是 `laocaimi.org` 的独立内容研发仓库。它负责 Research/Content，不直接承担生产网站运行。

## 当前版本

`v0.7.0-user-rules-compliance`

当前基础资产：

- 2406 个 brbcw 精选来源ID
- 2294 篇可识别技巧原子的来源
- 759 个方法家族、1389 个精细方法簇
- 1321 篇风险声明来源已隔离为未验证声称
- 玩法机制 / 平台经济参数双层规则系统
- 时时彩历史官方机制基线及位置同构规则
- 和值、跨度、频率、遗漏、奇偶、大小、重号、邻号等可执行分析指标
- 可复算案例引擎
- 正文生成前的文章蓝图、SEO结构、去重指纹和永久角度占位
- **90%金额 + 90%目标空间覆盖的用户内部硬门禁**
- **定码轮换三级玩法格式Registry与可执行语法校验**
- **用户研究指标体系的优先级与防过拟合验证协议**
- `caipiaowenzhang → fdsasaaa/xyptdq → www.laocaimi.org` 草稿发布协议

## 核心原则

1. **规则先于文案**：玩法机制核验后才能写合法投注案例；金额、奖金、返点、限额必须有具体平台 economics。
2. **用户内部策略与平台事实分层**：90%金额/覆盖门禁属于 internal policy，不能描述成某个平台官方规则。
3. **历史时时彩不是当前中国官方在售产品**：历史规则只作为玩法机制基线。
4. **分分彩等不得自动继承时时彩规则**：必须显式完成 provider / lottery / play mapping。
5. **统计指标不是预测保证**：冷热是频率，遗漏是间隔，和值与跨度是描述/筛选指标。
6. **来源文章不是事实库**：论坛命中率、稳赚、盈利说法不自动升级为事实。
7. **先蓝图、后正文**：搜索意图、技巧原子、案例算法、规则引用和去重指纹先确定，再写长文。
8. **idea 也参与永久去重**：通过 `--reserve` 占位的文章即使尚未写完，也会阻止未来生成同一角度。
9. **可执行投注案例也必须过合规门禁**：文章若携带 `normalized_bets`，质量审核会执行单方案、组合方案、跨玩法覆盖及高级倍投阶段检查。
10. **SEO必须有信息增量**：不为关键词变体批量制造低价值页面。
11. **生产隔离**：本仓库 → Approved Package → `fdsasaaa/xyptdq` → 迅睿CMS草稿 → 网站发布。

## 90% 投注组合硬门禁

用户提供的规则被保存为：`policies/BET_COMPLIANCE_POLICY.json`。

系统实现：`engine/compliance.py`。

核心要求：

- 单方案和多方案都检查；
- 先统一映射为 `target_space_id + covered_outcomes`；
- 同一期、同彩种、同目标中奖空间跨玩法合并；
- 覆盖号码先去重再计算；
- 总金额不得高于参考奖金的90%；
- 唯一目标结果覆盖率不得高于目标空间的90%；
- 高级倍投按 `phase_amounts` 分阶段检查；
- 缺少目标空间映射时 fail-closed；
- 违规时 `assert_exportable` 禁止导出。

> 这是一套用户定义的内部约束，不是任何平台官方规则的证据。

标准化投注协议：`schemas/normalized_bet.schema.json`。

CLI：

```bash
python -m engine.cli check-portfolio --file portfolio.json
```

## 定码轮换格式层

- `formats/dingma_rotation_v1.json`：一级类别 + 玩法类型 + 玩法名称的三级格式Registry
- `formats/dingma_rotation_counts_v1.json`：最大注数/组合空间的分层核验
- `engine/format_rules.py`：可执行语法校验

特别固定：

- 直选单式与直选复式使用不同格式；
- 五位置 `定位胆` 与单独万/千/百/十/个位使用不同格式；
- 组选包胆不能因只输入一个数字就按1注理解；
- 和值 `21` 是一个整体和值，不能拆成 `2 1`；
- 前四/后四组选、五星组选60/120、任二/任三/任四、和值、龙虎等平台行为仍按状态字段保留验证缺口。

数学层已经验证并编码：三星直选/组三/组六/混合组选/单胆码包胆、二星直选/组选/包胆、固定四星组选4/6/12/24，以及五星组选60/120的组合数学候选值。平台是否提供同名玩法仍需独立 mapping。

CLI：

```bash
python -m engine.cli validate-format \
  --play-type 前三 --play-name 直选复式 --content "089-145-689"
```

## 用户研究指标体系

用户上传的研究资料没有被当成“预测规则”，而是压缩为：

`knowledge/research/USER_RESEARCH_TAXONOMY_V1.json`

优先吸收：

- 数据完整性与规则版本分段；
- 定位频率、遗漏、和值、跨度、重号/邻号；
- 理论概率、蒙特卡洛基准、随机性审计；
- 时间顺序样本外、walk-forward、多段复验；
- 多重检验修正与失败实验记录。

高阶马尔可夫、神经网络、遗传算法大规模搜规则等标记为高过拟合风险；民间/文化型方法只允许作为 research-only 题材，默认假设是不优于同数量随机基准。

## 文章生成流水线

`方法家族 → 玩法规则校验 → case_plan → article blueprint → pre-draft dedup → reserve idea → draft → quality/SEO/compliance gate → approved package → xyptdq → CMS草稿 → published → 回写Registry`

完整说明：`docs/ARTICLE_GENERATION_PIPELINE.md`

### Blueprint 固定字段

正文生成前至少确定：

- article_id / blueprint_id
- provider / lottery / play
- technique family / technique atoms
- title / slug seed
- primary / secondary keywords
- search intent
- information gain type
- outline
- case structure / case plan
- rule refs / source refs
- fingerprint
- blockers / duplicate hits

如果技巧原子没有可执行案例算法，蓝图会标记 `blocked`；如果与历史文章高度重叠，则标记 `duplicate_blocked`。

## CLI 示例

```bash
python -m engine.cli audit

python -m engine.cli plan \
  --provider <provider_id> --lottery 时时彩 --play 后三直选 --count 10

python -m engine.cli blueprints \
  --provider <provider_id> --lottery 时时彩 --play 后三直选 --count 10 --reserve

python -m engine.cli case \
  --draw 12345 --draw 22346 --draw 92347 --draw 02348 \
  --selector 后三
```

## 玩法机制层

历史官方基线：`rules/mechanics/ssc/`

位置同构推导：`rules/mechanics/ssc_derived/`

当前包括定位胆、一星、前/后二、前/中/后三、前/后四、五星直选，以及二星/三星常见组选结构和后二大小单双。位置推导规则都要求 provider mapping，且不继承 economics。

## 分析与案例层

- `engine/analysis_metrics.py`
- `engine/casebook.py`
- `knowledge/TECHNIQUE_SEMANTICS.json`
- `schemas/article_case.schema.json`
- `docs/ARTICLE_CASE_STANDARD.md`

普通案例默认：

- `claim_scope = descriptive_only`
- `predictive_guarantee = false`

## 蓝图与永久记忆层

- `engine/blueprints.py`
- `engine/article_memory.py`
- `schemas/article_blueprint.schema.json`
- `registry/articles.jsonl`

正文尚未产生时就先做查重，是为了避免把Token和审核成本浪费在已写过的角度上。

## Provider 映射与Economics

- `schemas/provider_lottery_mapping.schema.json`
- `mappings/PROVIDER_MAPPING_POLICY.md`
- `schemas/economics_rule.schema.json`

即使 mechanics mapping 为 verified，金额、奖金、返点、最低投注单位和限额仍必须单独核验。

## 发布层

- 网站仓库：`fdsasaaa/xyptdq`
- CMS：迅睿CMS
- `schemas/publish_package.schema.json`
- `publishing/XYPTDQ_BRIDGE.md`

发布后必须把最终URL、发布日期、最终标题、内容Hash和fingerprint回写文章Registry。

## 测试

```bash
pytest -q
python -m engine.cli audit
```
