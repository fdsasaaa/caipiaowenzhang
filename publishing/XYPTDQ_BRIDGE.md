# caipiaowenzhang → xyptdq 发布桥梁

目标网站仓库：`fdsasaaa/xyptdq`（`www.laocaimi.org`，迅睿CMS）。

## 当前边界

- `caipiaowenzhang`：研究、规则、技巧知识、生成、查重、SEO、质量审核，最终产出 Approved Package。
- `xyptdq`：接收 Approved Package、再次校验、映射迅睿CMS栏目/字段、生成网站 Draft、显式排期、调用既有 Native Publisher、导出 Publication Receipt。
- 生产服务器：只负责网站运行和受控发布，不承担大规模内容生成。
- 内容引擎不得直接修改生产数据库或服务器。

## 当前正式分类合同

网站已经退休 `seo-articles`。所有普通 SEO / 技巧 / 研究型文章统一进入：

- `site_category_key=tzjq`
- CMS 展示栏目：`投注机巧`
- 数字 `catid` 仍由网站仓库 `config/content_category_map.json` 决定，内容引擎不得硬编码。

因此 `seo_topic` 也必须路由到 `tzjq`；任何新的 `seo-articles` package 都应 fail-closed。

## Approved Package 交付条件

只有 `status=approved` 的文章可以进入桥梁。未来自动跨仓库读取的唯一正式源目录是：

`articles/approved/`

每个包至少必须具备稳定身份、SEO和证据字段，包括：

- article_id
- title / slug / meta_description
- primary_keyword / secondary_keywords / search_intent
- content_type / site_category_key / tags
- content / content_format
- rule_refs / source_refs
- case_scope
- source_fingerprint / content_hash
- internal_links

## 网站侧生命周期

当前网站仓库已经具备并验证：

`Approved Package → ingress → Draft → explicit Scheduled → Native Publisher → Publication Receipt`

这意味着“跨仓库自动取稿”和“自动发布”必须保持为两个独立开关。

### 现在允许准备的能力

未来可以自动读取 `articles/approved/` 并把通过网站二次校验的 package 变成网站 Draft。

### 现在明确禁止的能力

- Approved Package 不能直接变成 Scheduled。
- 跨仓库同步不能直接调用 Native Publisher。
- 跨仓库同步不能自行生成 `publish_at`。
- 当前发布冻结未解除前，不得恢复 Publisher cron 或消费新文章发布队列。

## 幂等与防重复

跨仓库同步应至少以以下身份组合进行 fail-closed 校验：

- article_id
- source_fingerprint
- content_hash

同 article_id + 同 hash 允许幂等重复读取；同 article_id + 不同 hash 不得静默覆盖网站 Draft，必须回到 revision / re-Approval 生命周期。

## Publication Receipt

网站真正发布成功后，由 `xyptdq` 导出 Publication Receipt，再由本仓库显式导入 Registry。

只有 receipt 证明 CMS `published` 状态后，Registry 才记录：

- cms_id
- published_url
- published_at
- publication_receipt_id

Internal Link Planner 只有在目标文章拥有真实 `published_url` 后才能解析 URL；任何正文内链修改都会改变 content hash，因此必须重新 Approval。

## 当前状态

- 内容生成系统：v2.2.0。
- Approved Package → 网站 Draft 生命周期：已存在并验证。
- 自动跨仓库 transport：**尚未启用**。
- 网站自动文章发布：**冻结**。
- 当前正确准备方向：先让文章库持续积累 Approved 内容，同时保持网站 Draft-only / publication fail-closed；文章量和质量满足要求后，再分别启用 transport 与 scheduling/publishing。
