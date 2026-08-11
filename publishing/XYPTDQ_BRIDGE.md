# caipiaowenzhang → xyptdq 发布桥梁

目标网站仓库：`fdsasaaa/xyptdq`（`www.laocaimi.org`，迅睿CMS）。

## 边界

- `caipiaowenzhang`：研究、规则、技巧知识、生成、查重、SEO、质量审核。
- `xyptdq`：接收 approved package、映射迅睿CMS栏目/字段、生成草稿、部署。
- 生产服务器：只负责展示与运行，不承担大规模内容生成。

## 交付条件

只有 `status=approved` 的文章可以进入桥梁。每个包必须含：

- article_id
- title / slug / meta_description
- primary_keyword / secondary_keywords / search_intent
- category / tags
- content
- rule_refs / source_refs
- case_scope
- internal_links

## 安全门禁

1. `mechanics_only` 文章不得陈述未核验的单注金额、奖金、赔率、返点或平台限额。
2. `economics` 文章必须存在 provider-specific verified economics rule。
3. 网站仓库接收后先进入草稿，不默认立即公开。
4. 网站发布成功后必须把最终URL、发布时间和最终标题回写 `registry/articles.jsonl`，形成永久去重记忆。
5. 内容引擎不得直接修改生产数据库或服务器。

## 下一步

在 `xyptdq` 仓库新增一个轻量 importer，把本协议的 JSON package 映射到迅睿CMS草稿字段。该 importer 必须先在非生产数据上验证栏目、SEO字段、slug、正文和草稿状态映射，再接入自动发布。
