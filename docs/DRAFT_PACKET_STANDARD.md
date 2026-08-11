# Draft Packet Standard

Draft Packet 是 Article Blueprint 与最终正文之间的冻结层。任何AI、任何模型、任何写作代理在生成正文前，都必须读取 Packet，而不能直接从论坛来源或自由提示词开始写。

## 目标

1. 固定玩法、技巧、规则引用和来源引用；
2. 固定 SEO 标题、主关键词、搜索意图和 Meta Description；
3. 提供可复算案例数据；
4. 明确允许和禁止的事实陈述；
5. 把90%投注组合门禁传递到正文质量审核；
6. 让不同模型生成的文章仍遵守同一套底层事实。

## 案例规则

默认没有真实历史数据时，系统生成 `synthetic_validation` 五位数字样本。

正文必须原样出现：

`演示数据，不是真实开奖记录`

这种案例只用于解释计算步骤，不得写成历史实盘表现，也不得据此声称下一期更容易命中。

未来如果接入真实历史开奖，可将 case_type 换成 `historical`，但必须保存数据来源和时间范围。

## Economics 边界

`case_scope = mechanics_only` 时：

- 可以说明合法选号结构、位置、注数公式、中奖条件；
- 不得把未核验的赔率、返点写成事实；
- 可执行投注案例如果涉及金额，必须提供 `normalized_bets` 并通过合规门禁。

`case_scope = economics` 时仍要求 provider-specific verified economics rule。

## 来源使用

来源文章只能用于：

- 方法灵感；
- 历史案例线索；
- 术语和研究角度。

不得整段复制，不得把来源文章里的命中率、稳赚、盈利声明自动升级为事实。

## Draft Review

AI产出正文后，至少检查：

- required fields 是否齐全；
- 演示数据标签是否存在；
- rule_refs 是否和 Packet 完全一致；
- 是否出现稳赚/必中/包赢/100%中奖等保证性表述；
- mechanics_only 是否偷写未核验赔率/返点；
- 后续还要经过 `engine.quality.evaluate()`、重复检测和投注合规检查。

## CLI

```bash
python -m engine.cli draft-packets \
  --provider <provider_id> \
  --lottery 时时彩 \
  --play 后三直选 \
  --count 10
```

输出的 `packets[]` 可以直接作为未来AI写作任务输入。
