# 老彩迷内容引擎 Content Lifecycle v1

网站仓库：`fdsasaaa/xyptdq`

内容引擎：`fdsasaaa/caipiaowenzhang`

冻结日期：2026-08-11

本文件是当前内容生成、SEO归属、跨仓库草稿、未来发布回执与内链 revision 的正式接力说明。

## 1. 核心状态机

```text
Source Knowledge / Verified Mechanics
  ↓ Planner
Blueprint
  ↓ exact keyword ownership + dedup + rule capability
Draft Packet
  ↓ AI draft
Draft Review + Quality + SEO contract
  ↓ Approval
Approved Package
  ↓ website validator + converter
Website Draft
  ↓（当前冻结，不执行）explicit promote + publish_at
Website Scheduled
  ↓（未来）Native Publisher
CMS Published
  ↓ verified Publication Receipt v1
Content Registry Published
  ↓ real published_url
Internal Link Planner resolved target
  ↓ Internal Link Revision Gate
Draft Revision
  ↓ full re-Approval
New Approved Package with new content_hash
```

任何一步都不得跳过上一层的身份/hash/状态验证。

## 2. Source / Mechanics 边界

来源知识库用于：

- 选题家族；
- technique atoms；
- source support / source risk；
- 方法结构启发。

来源文章的盈利、命中、经验结论不会自动升级为事实。

玩法机制必须有 verified mechanics rule 才能形成确定性教程案例。经济参数没有 verified economics rule 时，不写具体赔率、返点、奖金或盈利承诺。

Synthetic case 只用于可复算机制演示，必须明确标记为演示数据，不是真实开奖记录。

## 3. Subject 与 Rule Scope

v1.1 起分离：

- `subject_lottery / subject_play`：文章在讲什么；
- `lottery / play`：底层规则验证作用域。

因此可以诚实表达“文章主题是分分彩”，同时不把通用规则伪装成已验证的分分彩平台经济规则。

## 4. Position Selector

v1.2 起 `position_filter` 被定义为 selector，而不是预测指标。

目标玩法先决定 selector；来源 positions 只证明该 selector 是否得到该来源家族支持。

必须避免：文章讲“后三”，案例却因为来源 positions 顺序而算“万位”。

## 5. Exact Primary Keyword Ownership v1.3

`engine/seo_keywords.py` 把 exact primary keyword 作为唯一占用资源。

四层门禁：

1. Blueprint；
2. reserve；
3. Approval；
4. registry audit。

Method article 的 canonical primary keyword 根据：

```text
subject lottery + subject play + technique atom modifier
```

派生。

当前第二批示例：

- `分分彩定位胆冷热技巧`
- `分分彩定位胆遗漏技巧`
- `分分彩后三组选3和值技巧`
- `分分彩后三直选跨度技巧`
- `分分彩后二大小单双技巧`

历史 Registry 行不重写；effective state 采用 append-only + last-write-wins，ownership audit 使用 canonical rule。

## 6. Registry

`registry/articles.jsonl` 是 append-only lifecycle log。

同一个 article_id 后写状态覆盖 effective view，但旧记录保留。

当前8篇有效状态均为 `approved`，并记录 website draft path。没有任何一篇被标记为 scheduled/published。

## 7. 网站 Draft Bridge

Approved Package 到网站时必须经过网站侧 defense-in-depth validator 与 converter。

当前8篇均已进入 `xyptdq/content/drafts/`，且：

- publication_state=draft；
- site_category_key=tzjq；
- catid=3；
- 无 publish_at；
- 未进入 modern managed scheduled；
- 未写生产 CMS。

网站 converter 支持显式 metadata-only refresh，但正文 bytes 发生变化时必须进入正式 revision workflow。

## 8. Website SEO Portfolio Defense

网站仓库也独立检查 exact primary keyword ownership。

现代 managed content 中：

- 两个不同 article_id 不得占同一个 normalized exact keyword；
- 同 article 跨 draft/scheduled 允许，但 keyword/fingerprint 必须一致；
- source content hash 必须证明 content bytes。

网站还有11个 bridge 建立前的 historical scheduled SEO canaries，它们由固定 article-key manifest grandfather，不能作为现代文章状态判断依据。

因此当前真实状态仍是：

```text
modern managed drafts = 8
modern managed scheduled = 0
modern managed published = 0
```

## 9. Internal Link Planner v1

`engine/internal_links.py` 只规划 `article_id → article_id`。

主要评分维度：

- 同 subject lottery；
- 同 exact subject play；
- 共享位置/玩法家族；
- shared technique atoms；
- 同 content type；
- target 已 published 时少量加分。

默认最低语义分45。同彩种本身不够，因此允许某篇暂时0条内链，不为数量硬塞弱相关链接。

未发布目标：

```json
{
  "resolution_status": "pending_published_url",
  "url": null
}
```

当前8篇全部处于这种 URL pending 状态。

## 10. Internal Link Revision Gate v1

真实 target `published_url` 出现后，也不能直接改 Approved Package。

`engine/link_revision.py`：

- 输入必须是 approved package；
- 原 content bytes 必须匹配原 content_hash；
- link plan 必须通过 audit；
- 只渲染 resolved target；
- 最多3条；
- 禁止 self / duplicate；
- anchor HTML escape；
- 只允许受验证的 laocaimi.org HTTPS URL；
- 在正文末尾追加 managed `相关阅读` 区块；
- 输出永远是 `status=draft`；
- `revision_reason=internal_links`；
- 记录 `revision_of_content_hash` 与 `proposed_content_hash`。

新正文必须完整重新走 Draft Review + Approval；Approval 后保留 revision ancestry，并产生新的 content_hash。

当前8篇因没有真实 published_url，Revision Gate 必须 fail-closed。

## 11. Published URL 合同

`engine/site_urls.py` 是内容引擎统一 URL validator。

允许：

- HTTPS `laocaimi.org` / `www.laocaimi.org` 的具体站内文章路径；
- 当前 Xunrui Native CMS 精确 show route：

```text
https://www.laocaimi.org/index.php?c=show&id=<positive integer>
```

如果存在 query，只允许该 route 的 `c=show` 与 canonical positive `id`，不能有额外/重复 query、fragment、credentials 或非443端口。

## 12. Publication Receipt v1

网站 `xyptdq` 已提供离线 exporter：

```text
scheduled JSON + publisher runtime state
  ↓
Publication Receipt v1
```

Exporter 会验证：

- modern managed scheduled identity；
- source body hash；
- runtime state 明确 published；
- cms_id / published_at；
- runtime publisher-level hash 与 exact scheduled JSON 一致。

内容引擎 `engine/publication_receipts.py` 再次验证：

- schema/type；
- deterministic receipt_id；
- article_id / article_key；
- fingerprint / content hash；
- publisher hash；
- source file；
- site base URL；
- cms_id 与 published URL 的精确映射；
- timezone；
- Registry 已存在该 article；
- fingerprint/content hash 与 Registry effective state 一致；
- article_key 与 `website_draft_path` 一致；
- 已 published 时不能出现 CMS ID / URL / receipt identity 冲突。

CLI：

```bash
python -m engine.cli publication-receipt --file receipt.json
```

默认只 validate + preview。

只有受信任的跨仓库 receipt 才可显式：

```bash
python -m engine.cli publication-receipt --file receipt.json --record
```

`--record` append-only 写入：

- status=published；
- cms_id；
- published_url；
- published_at；
- publisher_article_hash；
- publication_receipt_id；
- website_published_source_file。

Exact 重复 receipt 幂等 unchanged；冲突 receipt 拒绝。

### 重要信任说明

Publication Receipt v1 是字段/hash/runtime publication-state 的一致性合同，不是独立密码学签名。生产 `--record` 必须只接受从受信任网站仓库 / Server Bridge 取得的 receipt，不接受来源不明的手工 JSON。

## 13. Receipt → Internal Link 跨层闭环

测试已证明：

```text
valid receipt
  ↓ preview/record published Registry state
published_url becomes available
  ↓
Internal Link Planner target = resolved
  ↓
Revision Gate accepts exact native CMS URL
  ↓
draft revision + new content hash
  ↓
mandatory re-Approval
```

但没有对当前8篇制造或导入任何 fake receipt。

## 14. 当前8篇状态

第一批3篇：格式/组合数学烟测。

第二批5篇：真实 source-backed 技巧家族烟测。

总计：

- content-engine effective articles：8 approved；
- website modern managed drafts：8；
- modern managed scheduled：0；
- modern managed published：0；
- real publication receipts：0；
- resolved internal-link URLs：0。

## 15. 当前冻结边界

当前阶段继续遵守：

- 不批量发布新文章；
- 不自动 promote draft；
- 不调用 native publisher；
- 不写生产 CMS；
- 不伪造 published URL；
- 不提前插入会产生404的内链；
- 不把历史11个 pre-bridge scheduled 误算为当前8篇的排期状态。

## 16. 已合并能力节点

内容引擎：

- v1.1 subject/rule scope：`8d23714...`
- v1.2 selector / position_filter：`59b7140...`
- 第二批内容：`08d568a...`
- 第二批永久 Registry：`ffabb63...`
- exact keyword ownership v1.3：`73c99c039c3960cbc3a7bca82969a1ced7141b2c`
- Internal Link Planner v1：`56831f2d64c7e49887e07581b14637281a86f473`
- Internal Link Revision Gate v1：`f821a52178cab43f103031b172e20969b71e5c02`
- Publication Receipt importer v1：`69fdeeb987834de675e12decf7fc52ca149620dc`

网站：

- 8篇 smoke drafts 已进入 main；
- SEO metadata refresh：`f795fbe944b4758f0fcf5fa367289e452372dce6`
- SEO portfolio ownership audit：`7dbbe7d9e478cbb1d739b2a75adc554e87147a55`
- Publication Receipt exporter：`bc59d008ac51c6501b4e07f57249fff95d7baec1`

## 17. 下一阶段入口

在用户仍要求“文章发布冻结”期间，下一阶段应优先：

1. 继续扩充 verified mechanics / article families，而不是排期；
2. 做第三批 source-backed 草稿时继续遵守 exact keyword ownership 与 dedup；
3. 在更多文章形成后重新计算 Internal Link Planner 图；
4. 只有用户明确解除发布冻结，才开始设计 managed draft → scheduled 的真实批量运营节奏；
5. 第一篇真实发布后，用真实 Publication Receipt 验证反向桥，再允许任何 resolved internal-link revision。
