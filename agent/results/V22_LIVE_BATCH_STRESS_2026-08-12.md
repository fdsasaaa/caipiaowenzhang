# V2.2 多层文章真实 API 压力测试记录 — 2026-08-12

## 结论

本记录保存 `V2.2 multi-stage article pipeline` 对真实 OpenAI-compatible provider 的三轮五篇批次压力测试。

- Provider: `https://api.synapai.top/v1`
- Model: `gpt-5.4-mini`
- Secret: GitHub Actions `MODEL_PROVIDER_API_KEY`
- 调用方式: `/responses` + strict JSON Schema Structured Outputs
- 固定 Blueprint 数: 5
- 每轮均使用同一组 Blueprint、同一模型、同一筛选参数
- Registry write: **false**
- Website draft write: **false**
- Scheduled: **false**
- Published: **false**

最终真实批次达到 **4/5 approved**。第 5 篇的真实失败已定位为 Claim→Evidence 元数据归类问题，并在之后做了确定性离线修复与回归测试；按照成本控制约定，本轮没有进行第四次付费 API 重跑。因此：

> **V2.2 状态：candidate / not yet fully live-accepted.**
>
> V2.1 的单篇真实 100/100 acceptance 仍是当前已正式验证的稳定生产路径。V2.2 下一次只需要针对最终未通过的后二区选复式类案例做最小真实复验，再决定是否晋升为 fully live-accepted。

---

## 固定五篇 Benchmark

| Case | 主题 | 机器预冻结空间 |
|---|---|---|
| 001 | 后三直选：和值10–17 → 跨度3–7 | `1000 → 560 → 384` |
| 002 | 后三直选：恰好2个奇数 → 恰好1个大号 | `1000 → 375 → 132` |
| 003 | 后三直选：和值8–19 → 三位全异 | `1000 → 760 → 588` |
| 004 | 后二区选：0/3/6/8/9数字池 → 对子和值8–15 | `45 → 10 → 7` |
| 005 | 后二区选：0/2/5/7/9数字池 → 一奇一偶 | `45 → 10 → 6` |

所有 `before / after / excluded` 均由 `engine/filter_pipeline.py` 穷举，不交给模型自行计算。`experimental_parameter` 只表示实验前冻结的研究参数，不表示预测优势。

---

## Round 1 — 5/5生成，0/5批准

- Workflow run: `31549816077`
- Artifact ID: `9123865201`
- Artifact SHA256: `16b9a1c8994e7cbabc83f52698f02c9ba6260380dbcc7dffac5bd7ac3c0ae006`
- Requested: 5
- Generated: **5**
- Approved: **0**

重要观察：五篇全部 `quality_score=100`、`editorial_score=100`、`multistage_score=100`，失败全部发生在旧 Claim→Evidence 审核边界，而不是正文生成、多层数学或编辑价值。

Response IDs:

- 001: `resp_0c29ec24ddb0cd9a016a7bbc382b88819589eee94da46fefec`
- 002: `resp_09e2357bc916c1f7016a7bbc551648819b8ab9d21f118e7570`
- 003: `resp_07601cf852cccbeb016a7bbc76e880819a88992fb266418fe2`
- 004: `resp_09da98f99b1084c6016a7bbc97fdcc819aadffb8a4b5227eb0`
- 005: `resp_0af50d6385408eee016a7bbcb79f34819abb10e7aad37377c4`

主要暴露问题：

1. “不是命中率 / 不代表下一期”等否定性风险说明被误当成正向表现/预测声明；
2. 同一个 `45注→10注→7注` 数学关系在正文多处解释时，被要求机械复制多条 evidence；
3. 后二文章里参数数字（如 `0/2/5/7/9`）干扰了注数证据匹配；
4. 模型有时会给 editorial evidence 填入无意义 placeholder ref；
5. 演示数据免责声明的语义正确但不一定逐字等于旧固定句。

---

## Round 2 — 5/5生成，2/5批准

- Workflow run: `31550352524`
- Artifact ID: `9124064737`
- Artifact SHA256: `32eec3b22be902b25f0553d2e0d39d82ef3ffee27f585e5d38129bdff1223fa0`
- Requested: 5
- Generated: **5**
- Approved: **2**

通过：001、003。

Response IDs:

- 001: `resp_08f9771ddd188cda016a7bbe67b7a8819b96ed2f72740328fe`
- 002: `resp_0e6894961b38fa4f016a7bbe8d0e3c81949ae52e3a8ec78aa3`
- 003: `resp_04dbf2e80233b4d5016a7bbeab4cec81968815d5665f66fb38`
- 004: `resp_02997dfa4fabbafa016a7bbecd07e48193b70cbaae3beffb89`
- 005: `resp_011693d9d226edfc016a7bbeec94488199aed22cb352426c66`

这一轮验证了第一轮修正有效，但继续暴露：

- “不在说命中率更高”属于自然否定表达，需要语义识别；
- 量化证据匹配应只比较 `10注/35注` 这类带单位数量，不能把候选池裸数字当成独立硬事实；
- 同一句可能同时复述第一层与第二层数量，需要允许由多条已验证 calculation evidence 的并集覆盖；
- 如果模型真的漏写明确“非真实开奖记录”披露，系统应确定性补入标准安全标签，而不是放松免责声明要求。

---

## Round 3 — 最终付费复测：5/5生成，4/5批准

- Workflow run: `31550821889`
- Artifact ID: `9124243143`
- Artifact SHA256: `eba7dd87aeb0640e52b6c75001c61323c02f998c78fbdd3432044f577a5ab2c9`
- Requested: 5
- Generated: **5**
- Approved: **4**
- Failed: **1**

### 001 — PASS

- hard quality: `100`
- editorial: `100`
- multistage: `100`
- errors: `[]`
- response: `resp_0c23e3e8485c0e4d016a7bc03edc7c819bb94f1890c3a45e40`

### 002 — PASS

- hard quality: `100`
- editorial: `100`
- multistage: `100`
- errors: `[]`
- response: `resp_03810a5053147ed7016a7bc07cee8c8194809e9a291fe7cfce`

### 003 — PASS

- hard quality: `100`
- editorial: `100`
- multistage: `100`
- errors: `[]`
- response: `resp_0eed2bf663debf03016a7bc0a0ff288191995fe7847bb3da4d`

### 004 — FAIL（仅 Claim→Evidence 元数据）

- hard quality: `100`
- editorial: `100`
- multistage: `100`
- response: `resp_0bbca3d31cc7b9b5016a7bc0c68b48819bae634a6a7f8ad960`

真实失败：模型把系统 `filter_pipeline` 的确定性空间计算写成 `support_type=synthetic_case`，并同时引用 `case_bundle + rule_ref`。旧 gate 正确拒绝了这种混合 evidence metadata。正文、多层空间、演示免责声明本身均正确。

随后离线修正为：

- pipeline `before/after/excluded` evidence 改为**系统自有**，由引擎从机器枚举结果确定性注入；
- 只有能精确对应某个机器已知 stage/overall 数学关系的错误模型 evidence 才允许规范化；
- 与 pipeline 不匹配的 synthetic claim 仍不会被静默改写，继续由严格门禁拒绝；
- 对无序组选同时注入“个”与“注”口径的标准 evidence，支持正文自然复述。

该修正已加入回归测试，但**没有再进行第四轮付费 API 测试**。

### 005 — PASS

- hard quality: `100`
- editorial: `100`
- multistage: `100`
- errors: `[]`
- response: `resp_0b0d30ceb2e663db016a7bc0e581508196a81f11aeaeae0675`

---

## 本轮形成的系统能力

1. 多层筛选参数在看到演示样本前冻结；
2. 候选空间逐层穷举计算，不由LLM心算；
3. 每层必须真正减少候选空间；
4. 正文必须展示每层 `before → after → excluded`；
5. `experimental_parameter` 不可包装成预测优势；
6. source hypothesis 与系统数学明确分离；
7. 风险否定句与正向命中率/预测声明分离；
8. 重复实操解释可复用同一组已验证数量事实；
9. 演示数据免责声明由系统兜底注入；
10. pipeline calculation evidence 从模型控制权中移出，改为系统确定性生成。

---

## 安全与成本收尾

- 本轮共执行三次五篇真实 batch；第三轮后停止继续重跑；
- 临时 `.github/workflows/live-batch-v22-temp.yml` 已删除；
- 临时 `.github/live-batch-v22.trigger` 已删除；
- 不存在该 V2.2 测试留下的自动付费 push trigger；
- API key 从未写入仓库或日志；
- 本轮没有写 Registry、没有写网站 draft、没有 scheduled/published。

## 晋升条件

V2.2 不应因为离线修复就宣称已经 5/5 live accepted。建议下一次需要真实生成时，只针对后二区选复式类做一个最小 targeted smoke；若该类通过，再把 V2.2 状态从 `candidate` 晋升为 `fully_live_accepted`。
