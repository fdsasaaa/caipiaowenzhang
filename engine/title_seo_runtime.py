from __future__ import annotations

from typing import Iterable

from .title_seo import (
    TITLE_SEO_CONTRACT_VERSION,
    TitleSEOReview,
    evaluate_title_seo,
    formal_title_records,
    load_title_policy,
    plain_text,
)


def _topic_label(record: dict) -> str:
    primary = str(record.get("primary_keyword") or "").strip()
    for prefix in ("分分彩", "时时彩"):
        if primary.startswith(prefix):
            primary = primary[len(prefix):]
            break
    for suffix in ("投注技巧", "技巧", "方法", "教程", "筛选步骤", "筛选顺序", "注数计算", "参数设置", "演示案例"):
        if primary.endswith(suffix):
            primary = primary[:-len(suffix)]
            break
    primary = primary.strip(" ：:，,。")
    if primary:
        return primary
    play = str(record.get("subject_play") or record.get("play") or "这套玩法").strip()
    return play or "这套筛选思路"


def _body_focus(record: dict) -> str:
    content = plain_text(record.get("content"))
    for marker in (
        "停止条件", "常见误区", "候选空间", "参数预注册", "样本外验证", "组合数学",
        "风险边界", "输入输出", "复算", "注数", "遗漏", "冷热", "和值", "跨度",
    ):
        if marker in content:
            return marker
    return "规则边界"


def suggest_title_candidates(record: dict, count: int = 5) -> list[str]:
    """Build diverse candidates only after completed body/summary/search intent exist.

    No numeric hook is invented here. If a future model-generated candidate contains a
    number, TITLE_NUMERIC_CLAIM_VERIFIED still has to trace it to article/rule evidence.
    """
    topic = _topic_label(record)
    play = str(record.get("subject_play") or record.get("play") or "这一玩法").strip()
    angle = str(record.get("information_gain_type") or "")
    focus = _body_focus(record)
    pools = {
        "space_math": [
            f"候选空间为什么会变？{topic}的计算过程一次理清",
            f"先算注数，再谈{topic}：组合数学能说明到哪一步",
            f"从输入到结果：{topic}的空间计算与{focus}",
            f"{topic}怎么算才不混淆？复核候选空间的关键点",
            f"看懂{play}的{topic}，先分清计算结果和预测结论",
        ],
        "execution_checklist": [
            f"做到哪一步应该停？{topic}的复核清单",
            f"{topic}怎么检查才不漏步骤？先看输入、输出和停止条件",
            f"从规则到复核：{play}这套筛选流程最容易错在哪里",
            f"先固定步骤，再看结果：{topic}的执行边界",
            f"{topic}不是越筛越好，关键在什么时候停止",
        ],
        "parameter_boundary": [
            f"哪些参数能提前固定？{topic}的边界先说清",
            f"来源经验和系统参数有什么区别？用{topic}拆开看",
            f"从参数到结果：{topic}哪些能预设，哪些不能事后改",
            f"{topic}为什么不能看完结果再调？常见误区与风险边界",
            f"先定规则还是先看样本？{play}参数问题这样区分",
        ],
        "multistage_order": [
            f"先后顺序为什么重要？{topic}的多层筛选这样复核",
            f"从第一层到最后一层：{topic}的输入输出与停止边界",
            f"{topic}的关键不只是筛选，顺序和停止条件同样重要",
            f"为什么不能随意换顺序？用{topic}看连续筛选逻辑",
            f"做到最后一层之后呢？{topic}为什么不该继续追加条件",
        ],
        "sample_provenance": [
            f"演示样本能说明什么？{topic}别被当成预测结论",
            f"从演示数据到结果：{topic}的证据边界在哪里",
            f"{topic}里的样本结果从哪来？先分清计算与预测",
            f"先看样本怎么生成，再谈{topic}能不能被复现",
            f"{play}的{topic}为什么必须标清演示数据来源",
        ],
        "mechanics_case": [
            f"这一步到底怎么算？用{topic}把规则和复算过程讲清",
            f"从玩法规则到完整案例：{topic}应该怎样复核",
            f"{topic}为什么容易算错？关键在输入、计算和{focus}",
            f"先看规则，再看案例：{play}里的{topic}怎样正确理解",
            f"看懂{topic}不靠口诀，先把计算逻辑拆开",
        ],
    }
    values = list(pools.get(angle) or [
        f"{topic}到底在研究什么？先把规则和边界说清",
        f"从规则到复盘：{topic}应该怎样验证才不越界",
        f"先看复算过程，再谈{topic}：哪些结论不能直接推出",
        f"{topic}为什么容易被误读？从方法到风险边界",
        f"看懂{play}里的{topic}，先分清事实、计算和推断",
    ])
    maximum = max(3, min(int(count or 5), 5))
    return list(dict.fromkeys(values))[:maximum]


def _context(article: dict, packet: dict | None) -> dict:
    context = dict(article)
    if not packet:
        return context
    seo = packet.get("seo") or {}
    facts = packet.get("immutable_facts") or {}
    contract = packet.get("article_angle_contract") or {}
    context.setdefault("primary_keyword", seo.get("primary_keyword"))
    context.setdefault("search_intent", seo.get("search_intent"))
    context.setdefault("subject_lottery", facts.get("subject_lottery") or facts.get("lottery"))
    context.setdefault("subject_play", facts.get("subject_play") or facts.get("play"))
    context.setdefault("play", facts.get("play"))
    context.setdefault("technique_atoms", facts.get("technique_atoms") or [])
    context.setdefault("information_gain_type", contract.get("angle_type") or facts.get("information_gain_type"))
    return context


def apply_title_seo(
    article: dict,
    *,
    packet: dict | None = None,
    comparison_records: Iterable[dict] | None = None,
    evidence_source: dict | None = None,
    regenerate_candidates: bool = False,
) -> TitleSEOReview:
    """Generate 3-5 candidates from completed body and select only a gate-passing title."""
    policy = load_title_policy()
    context = _context(article, packet)
    current = article.get("title_candidates")
    candidates = [str(value).strip() for value in current or [] if str(value).strip()]
    if regenerate_candidates or not (int(policy["candidate_min"]) <= len(candidates) <= int(policy["candidate_max"])):
        candidates = suggest_title_candidates(context, int(policy["candidate_max"]))
    candidates = list(dict.fromkeys(candidates))[: int(policy["candidate_max"])]

    article["title_candidates"] = candidates
    article["title_seo_contract_version"] = TITLE_SEO_CONTRACT_VERSION
    article["title_selection_reason"] = (
        "正文完成后生成候选；按主题匹配、重复度、关键词结构多样性、数字真实性、搜索意图和可读性Gate选择。"
    )
    comparisons = list(comparison_records) if comparison_records is not None else formal_title_records()

    first_review: TitleSEOReview | None = None
    selected: str | None = None
    selected_review: TitleSEOReview | None = None
    for candidate in candidates:
        probe = dict(article)
        probe["title"] = candidate
        probe["seo_title"] = candidate
        review = evaluate_title_seo(
            probe,
            packet=packet,
            comparison_records=comparisons,
            evidence_source=evidence_source,
            policy=policy,
        )
        first_review = first_review or review
        if review.passed:
            selected = candidate
            selected_review = review
            break

    if selected is None:
        selected = candidates[0] if candidates else str(article.get("title") or article.get("seo_title") or "").strip()
        selected_review = first_review

    article["title"] = selected
    article["seo_title"] = selected
    final_review = evaluate_title_seo(
        article,
        packet=packet,
        comparison_records=comparisons,
        evidence_source=evidence_source,
        policy=policy,
    )
    article["title_review"] = final_review.as_dict()
    return final_review
