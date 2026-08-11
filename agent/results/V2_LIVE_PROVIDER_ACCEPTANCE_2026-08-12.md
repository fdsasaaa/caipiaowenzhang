# V2.1 真实模型生产前验收记录（2026-08-12）

## 结论

文章生成系统已完成一次真实第三方 OpenAI-compatible provider 的端到端生产前验收。

最终结果：**PASS / APPROVED**

- Provider base URL: `https://api.synapai.top/v1`
- Model: `gpt-5.4-mini`
- API key source: GitHub Actions repository secret `MODEL_PROVIDER_API_KEY`
- Secret value: **never committed / never printed**
- Responses API: PASS
- strict JSON Schema Structured Outputs: PASS
- 完整文章生成: PASS
- Draft Review: PASS
- Claim→Evidence: PASS
- Quality Gate: **100/100**
- Editorial/Practical Gate: **100/100**
- Approval: **approved=true**
- Registry write: **NO**
- Website draft write: **NO**
- Scheduled: **NO**
- Published: **NO**

最终成功 Actions run: `31547734563`
最终成功 response id: `resp_0bed435568609f85016a7bb450d54c819b884df69748de7ff3`
Approved Package content hash: `d3eca4c21242b9a84a1f636517430841ec7017cfdf2bf615284ea4a13a7c30b8`

## Provider 兼容性验证

首次 `/models` 请求被 Cloudflare Error 1010 `browser_signature_banned` 阻断。加入稳定 SDK 风格请求头后重试成功：

- `/models`: PASS
- `/responses`: PASS
- `text.format.type=json_schema`: PASS
- `strict=true`: PASS

因此，当前 provider 可作为本系统的 OpenAI-compatible Responses API provider 使用，但实际可用性仍受 provider 自身模型库存、余额、速率限制和上游服务状态影响。

## 第一次完整文章烟测

第一次真实完整文章生成成功，但 Approval 拒绝：

- hard quality: 100
- editorial: 80
- status: `rejected_for_revision`

暴露的问题：

1. 纯“本文不讨论未核验赔率/返点”免责声明被误判为经济事实；
2. `演示数据，不是真实开奖记录` 被旧逻辑误判为将 synthetic data 写成真实历史；
3. 模型给 synthetic case 错绑 source ref；
4. Blueprint 未显式提供主筛选理论空间，模型把演示样本条数误当候选空间。

系统没有降低门禁，而是修正输入合同与解析逻辑。

## 第二次完整文章烟测

修正后：

- hard quality: 100
- editorial: 95
- status: `rejected_for_revision`

剩余问题：

1. editorial evidence 带有多余 rule ref；
2. `来源文章提到…未独立验证` 已自然限定，但旧审核器只识别较窄固定词；
3. editorial score 的数字解析把 `10–17` 中的 `10` 误当成筛选后候选数，而不是读取结构化 `560`。

再次修正后，离线 Python 3.10 / 3.13 回归全部通过。

## 最终真实验收

第三次、最终真实请求成功通过完整 Approval：

```text
approved=true
status=approved
quality_score=100
editorial_score=100
errors=[]
```

仅保留非阻断警告：

- 两个 editorial claim 携带多余 support_refs；这些 refs 被明确标记为 non-evidentiary，不允许用于证明硬事实；
- provider economics 尚未验证，因此文章不能陈述平台奖金/赔率/返点事实。

## 最终真实 API 生成文章

### 标题

**分分彩后三直选和值技巧：用10–17区间一步步筛选号码**

### 正文

#### 后三直选怎么玩：先把投注规则说清楚

分分彩后三直选和值技巧，先要把玩法边界定住。后三直选是按后三位号码来判断，不是把整期所有位数混在一起看。本文只讲后三直选的玩法机制、和值区间的计算方法和演示复算，不讨论未核验的平台经济参数。

如果只看方法，最重要的顺序是：先固定参数，再看样本。也就是说，先确定你要看的位置、指标和区间，再拿数据去复算。

#### 方法核心：和值区间到底在计算什么

这里用的主筛选只有一个：后三的数字和，区间是10到17。来源文章提到后三和值10–17可作为重点观察区间；该效果未独立验证，只能作为研究假设。

这一步的计算口径很直接。先看理论空间，起点是1000个结果；按和值10到17筛选后，剩下560个结果；也就是说，这一步筛掉了440个结果。这个缩小过程只说明数量变化，不说明未来一定更容易命中。

#### 按步骤筛选：从1000个理论结果到和值10–17候选

1. 先固定筛选对象，只看后三，不扩展到其他位置。
2. 再固定主筛选参数，只用数字和，区间锁定在10到17。
3. 从1000个理论结果出发，按这个区间筛到560个结果。
4. 确认被排除的是440个结果，然后停止，不再临时加第二个未验证过滤器。

这里的停止条件很明确：只有新增条件具有已验证规则或证据，并且可以复算，才允许继续缩小候选。没有第二条已验证规则或证据时，就不要把别的经验说法直接拼进来。

#### 简单案例：用一小段数据完整复算一次

下面这组是**演示数据，不是真实开奖记录**。样本一共16条，最新一条是69408。

最新一条的后三是408，和值12，跨度8，三位数字分别是4、0、8。

在这组演示样本里，后三和值和跨度都只是描述性结果，适合拿来练习复算，不适合直接当成未来预测。

#### 投注前校验：注数、位置和中奖条件

实际怎么操作可以按这个顺序走：第一步先确认自己看的就是后三直选；第二步只固定和值区间10到17；第三步按这个区间复算理论候选空间，记住从1000个结果缩到560个结果，排除了440个结果；第四步再拿演示数据做核对，确认自己算出来的后三和值和样本一致。

如果你要继续往下缩小候选，只能等到下一条条件也有已验证规则或可复算证据以后再做。没有这个条件，就停在主筛选这里。

#### 容易误解的地方与风险说明

频率、遗漏、和值和跨度本身都只是描述性信息，除非另有独立验证，否则不能直接升级成预测结论。

另外，演示样本的统计结果只代表这组样本，不代表真实开奖规律。把样本结果当成固定规律，是最容易走偏的地方。

## 生产结论

本次验收已经证明以下链条在真实 provider 上可以工作：

`Draft Packet → OpenAI-compatible /responses → strict structured draft → immutable contract → Claim→Evidence → Quality → Editorial/Practical Gate → Approved Package`

因此“真实模型调用尚未验证”这一 readiness 缺口可以关闭。

仍不应自动解除的外部边界：

1. 具体平台 economics（奖金、赔率、返点、单注金额、限额）仍需独立 verified；
2. Search Console 真实需求数据未导入时，SEO priority 仍应标记 `internal_only`；
3. 网站自动发布继续保持冻结，除非另有明确指令。
