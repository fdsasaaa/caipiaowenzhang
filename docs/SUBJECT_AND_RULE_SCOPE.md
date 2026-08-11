# Article Subject 与 Rule Scope 分离

从 v1.1.0 起，文章引擎明确区分两个概念。

## Article Subject

- `subject_lottery`
- `subject_play`

回答：**这篇文章在讲什么？**

用于标题、SEO关键词、去重、内容规划、内链和长期文章记忆。

例如一篇文章可以是：

- `subject_lottery=分分彩`
- `subject_play=前三直选`

## Rule Scope

- `lottery`
- `play`
- `provider_id`
- `rule_refs`

回答：**当前事实具体被哪些已验证规则支持？**

如果文章只使用“通用五位数格式/组合数学”，Rule Scope 可以是通用规则，甚至在人工机制文章中保持空值；这不影响文章主题明确写“分分彩”。

## 为什么必须分开

“文章讨论分分彩”并不自动证明：

- 某个分分彩平台的奖金；
- 返点；
- 最低投注单位；
- 平台限额；
- 某个具体软件字段行为；
- 某种历史结构具有未来预测优势。

这些事实仍必须由 `rule_refs` / provider verification 单独支持。

## 数据流

`Plan → Blueprint → Draft Packet → Approval → Registry`

subject 字段在 Blueprint 阶段确定，进入 Draft Packet 后冻结。AI如果显式返回不同 subject，Draft Review 会拒绝。

Approved Package 同时保留 subject 和 rule scope，因此网站、SEO和去重可以知道文章主题，而规则审计仍能知道事实证据来自哪里。

## 向后兼容

旧记录没有 subject 字段时，Dedup 自动回退到 `lottery/play`。

第一批 smoke batch 的3篇机制文章通过 append-only Registry 更新补充 subject 字段，旧历史记录没有被改写。
