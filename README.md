# 老财迷彩票内容引擎（caipiaowenzhang）

这是 `laocaimi.org` 的独立内容研发仓库。它负责 Research/Content，不直接承担生产网站运行。

## 当前版本

`v0.6.0-article-blueprints`

当前基础资产：

- 2406 个 brbcw 精选来源ID
- 2294 篇可识别技巧原子的来源
- 759 个方法家族、1389 个精细方法簇
- 1321 篇风险声明来源已隔离为未验证声称
- 玩法机制 / 平台经济参数双层规则系统
- 时时彩历史官方机制基线及位置同构规则
- 和值、跨度、频率、遗漏、奇偶、大小、重号、邻号等可执行分析指标
- 可复算案例引擎
- **正文生成前的文章蓝图、SEO结构、去重指纹和永久角度占位**
- `caipiaowenzhang → fdsasaaa/xyptdq → www.laocaimi.org` 草稿发布协议

## 核心原则

1. **规则先于文案**：玩法机制核验后才能写合法投注案例；金额、奖金、返点、限额必须有具体平台 economics。
2. **历史时时彩不是当前中国官方在售产品**：历史规则只作为玩法机制基线。
3. **分分彩等不得自动继承时时彩规则**：必须显式完成 provider / lottery / play mapping。
4. **统计指标不是预测保证**：冷热是频率，遗漏是间隔，和值与跨度是描述/筛选指标。
5. **来源文章不是事实库**：论坛命中率、稳赚、盈利说法不自动升级为事实。
6. **先蓝图、后正文**：搜索意图、技巧原子、案例算法、规则引用和去重指纹先确定，再写长文。
7. **idea 也参与永久去重**：通过 `--reserve` 占位的文章即使尚未写完，也会阻止未来生成同一角度。
8. **禁止换皮重复**：只换标题、号码或同义词但核心方法相同，仍视为重复。
9. **SEO必须有信息增量**：不为关键词变体批量制造低价值页面。
10. **生产隔离**：本仓库 → Approved Package → `fdsasaaa/xyptdq` → 迅睿CMS草稿 → 网站发布。

## 文章生成流水线

`方法家族 → 玩法规则校验 → case_plan → article blueprint → pre-draft dedup → reserve idea → draft → quality/SEO gate → approved package → xyptdq → CMS草稿 → published → 回写Registry`

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

# 查看候选方法
python -m engine.cli plan \
  --provider <provider_id> --lottery 时时彩 --play 后三直选 --count 10

# 生成文章蓝图，但不写Registry
python -m engine.cli blueprints \
  --provider <provider_id> --lottery 时时彩 --play 后三直选 --count 10

# 生成蓝图并把可用角度永久占位为 idea
python -m engine.cli blueprints \
  --provider <provider_id> --lottery 时时彩 --play 后三直选 --count 10 --reserve

# 可复算统计案例
python -m engine.cli case \
  --draw 12345 --draw 22346 --draw 92347 --draw 02348 \
  --selector 后三
```

## 玩法机制层

历史官方基线：`rules/mechanics/ssc/`

位置同构推导：`rules/mechanics/ssc_derived/`

当前包括定位胆、一星、前/后二、前/中/后三、前/后四、五星直选，以及二星/三星常见组选结构和后二大小单双。位置推导规则都要求 provider mapping，且不继承 economics。

## 分析与案例层

- `engine/analysis_metrics.py`：和值、跨度、频率、遗漏、奇偶、大小、重号、邻号
- `engine/casebook.py`：可复算案例数据包
- `knowledge/TECHNIQUE_SEMANTICS.json`：技巧原子计算定义与文案边界
- `schemas/article_case.schema.json`：案例数据协议
- `docs/ARTICLE_CASE_STANDARD.md`：案例标准

普通案例默认：

- `claim_scope = descriptive_only`
- `predictive_guarantee = false`

## 蓝图与永久记忆层

- `engine/blueprints.py`：确定性文章蓝图生成
- `engine/article_memory.py`：把 ready 蓝图占位到文章Registry
- `schemas/article_blueprint.schema.json`：蓝图数据协议
- `registry/articles.jsonl`：idea / draft / approved / published 的长期去重事实源

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
