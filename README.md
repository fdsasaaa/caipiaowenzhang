# 老财迷彩票内容引擎（caipiaowenzhang）

这是 `laocaimi.org` 的独立内容研发仓库。它不是网站生产仓库，而是用于长期维护：

- 彩票玩法与投注规则库（规则优先、来源可追溯）
- 彩票技巧来源库与“技巧原子”库
- 已生成/已发布文章永久登记与去重
- Google SEO 文章规范
- 案例与数学校验
- 草稿 → 审核 → 发布的内容流水线

## 核心原则

1. **规则先于文案**：玩法、注数、中奖条件、赔率/奖金、返点等未核验时，不生成确定性描述。
2. **来源文章不是事实库**：论坛/历史文章中的命中率、稳赚、倍投收益等只作为“待验证观点”。
3. **禁止换皮重复**：标题不同但核心技巧、案例结构和搜索意图高度重合，也视为重复。
4. **案例必须可复算**：例子需标明玩法、选号、注数计算和中奖条件；不能把示例包装成盈利承诺。
5. **SEO 服务于信息价值**：不为关键词堆砌而生产页面，不制造无新增价值的大规模近重复内容。
6. **生产隔离**：本仓库负责 Research/Content；网站仓库负责 Publishing；生产服务器负责展示。

## 仓库状态

当前版本：`v0.1.0-bootstrap`

当前阶段：搭建内容引擎骨架。原始采集文章尚未进入仓库；在来源数据导入前应先确认仓库为 Private。

## 快速开始

```bash
python -m engine.cli init
python -m engine.cli status
python -m engine.cli audit
```

导入 brbcw 精选资料：

```bash
python scripts/import_brbcw.py /path/to/brbcw_有价值文章_筛选版.zip --output knowledge/source_manifests/brbcw.jsonl
python -m engine.cli rebuild
```

> 导入脚本默认只生成结构化来源清单，不会把论坛全文直接写入 Git。原始资料建议保留在受控存储中。

## 目录

- `SYSTEM.md`：未来任何 AI/Codex/WorkBuddy 的总接管协议
- `AGENTS.md`：仓库工程规则
- `rules/`：玩法与平台规则
- `knowledge/`：来源清单、技巧原子
- `registry/`：文章/技巧永久登记
- `seo/`：laocaimi.org SEO 配置
- `engine/`：去重、校验、质量门禁、索引
- `articles/`：草稿/审核/发布/拒绝生命周期
- `schemas/`：结构化数据协议
- `tests/`：本地自动测试

## 发布架构

`Content Engine（本仓库） → Approved Draft → 网站 GitHub 仓库 → WordPress/发布器 → laocaimi.org`
