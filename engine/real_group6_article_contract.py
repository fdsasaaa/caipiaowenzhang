from __future__ import annotations

from dataclasses import dataclass, field

from .ai_generation import build_generation_prompt
from .draft_packets import build_draft_packet
from .group_mode_binding import SYSTEM_BINDING, bind_group_mode

ARTICLE_ID = "VAL-RK-GROUP6-FAM-F8EFC151-V1"
FAMILY_ID = "FAM-f8efc151837be787"
SOURCE_REF = "BRBCW-004115"
PRIMARY_KEYWORD = "分分彩后三组六技巧"

SOURCE_BOUNDARY = (
    "BRBCW-004115只支持该家族包含组选类方法原子的来源归属；本例选择组六是系统在查看演示样本前预先冻结的验证选择，"
    "不是来源原文指定或推荐的组六模式，也不代表预测优势。"
)

DOMAIN_BOUNDARY = (
    "组六的120个无序投注单位组成整个组六目标域；每个单位覆盖6个有序排列，因此对应720个组六结构的有序开奖结果。"
    "720/1000=72%只表示组六结构占全部三位有序结果的比例，不是本项目的可执行投注覆盖率；"
    "若把120个单位全部使用，对组六目标域覆盖率是100%，超过90%上限，因此本文不得把“全120单位”写成可执行投注方案。"
)


class RealGroup6ArticleContractError(ValueError):
    pass


@dataclass
class RealGroup6ArticleQualityReport:
    passed: bool
    score: int
    errors: list[str] = field(default_factory=list)


def build_real_group6_blueprint() -> dict:
    binding = bind_group_mode(
        FAMILY_ID,
        group_mode="组六",
        binding_basis=SYSTEM_BINDING,
        frozen_before_observation=True,
    )
    if binding["group_mode"] != "group6":
        raise RealGroup6ArticleContractError("validation binding drifted away from group6")
    if binding["all_domain_units_executable_portfolio_allowed"] is not False:
        raise RealGroup6ArticleContractError("full group6 domain must not be executable under the 90% target-play ceiling")

    return {
        "blueprint_id": "BP-" + ARTICLE_ID,
        "article_id": ARTICLE_ID,
        "provider_id": "research-validation-only",
        "lottery": "时时彩",
        "play": "后三组选6",
        "subject_lottery": "分分彩",
        "subject_play": "后三组六",
        "content_type": "technique_article",
        "site_category_key": "tzjq",
        "technique_family": FAMILY_ID,
        "technique_atoms": ["group3_group6"],
        "resolved_selector": "后三",
        "selector_basis": "verified_group6_play",
        "angle_signature": "real-family-system-prefrozen-group6-domain-explanation",
        "title": "分分彩后三组六技巧：120个组选单位和720种排列怎么理解",
        "slug_seed": "ffc-last3-group6-120-units-720-orders",
        "primary_keyword": PRIMARY_KEYWORD,
        "secondary_keywords": ["分分彩组六", "后三组六", "组六投注技巧", "组六号码结构"],
        "search_intent": "学习分分彩后三组六的投注单位、排列覆盖和来源边界",
        "information_gain_type": "real_family_provenance_plus_verified_group6_domain_explanation",
        "summary_goal": (
            "说明真实家族只提供 broad 组选方法来源归属，系统预冻结组六作为验证模式；"
            "解释120个无序组六单位、每个6种排列、720个有序组六结果及三同号/组三边界，"
            "同时明确72%不是可执行投注覆盖率，全部120单位对组六目标域是100%覆盖并被执行门禁禁止。"
        ),
        "outline": [
            "先说清来源边界：来源只支持 broad 组选方法，组六是系统验证选择",
            "什么是组六：三个数字互不相同",
            "为什么组六只有120个无序投注单位",
            "一个单位为什么对应6个有序排列",
            "120个单位为什么对应720个组六结构的有序结果",
            "112为什么是组三、777为什么既不是组六也不是组三",
            "72%为什么只是结构占比，不是合规投注覆盖率",
            "为什么全文可以解释完整域，但不能把全120单位写成投注方案",
        ],
        "case_structure": "selector=后三;group_mode=group6;domain=unordered_group_units;scope=mechanics_only;mode_owner=system_research",
        "case_scope": "mechanics_only",
        "rule_refs": [binding["rule_ref"]],
        "source_refs": [SOURCE_REF],
        "source_support_count": 57,
        "source_risk_rate": 0.439,
        "fingerprint": "rk-group6-fam-f8efc151-v1",
        "status": "ready_for_draft",
        "blockers": [],
        "article_status": "validation_only_unregistered_identity",
        "editorial_contract_version": "1.1",
        "seo_requirements": {
            "plain_chinese": True,
            "example_required": True,
            "unique_information_gain_required": True,
            "registry_keyword_reservation": False,
            "avoid_keyword_stuffing": True,
            "avoid_guaranteed_outcomes": True,
        },
        "group6_validation": {
            "binding": binding,
            "source_boundary": SOURCE_BOUNDARY,
            "domain_boundary": DOMAIN_BOUNDARY,
            "group6_unit_count": 120,
            "ordered_group6_outcome_count": 720,
            "global_structure_share": 0.72,
            "target_play_full_domain_coverage": 1.0,
            "target_coverage_ceiling": 0.90,
            "full_domain_executable_portfolio_allowed": False,
            "example_unit": [1, 2, 3],
            "example_permutations": ["123", "132", "213", "231", "312", "321"],
            "group3_counterexample": "112",
            "triple_same_counterexample": "777",
            "must_list_all_120_units": False,
            "normalized_bets_allowed": False,
        },
    }


def build_real_group6_article_packet() -> dict:
    blueprint = build_real_group6_blueprint()
    packet = build_draft_packet(blueprint)
    packet["real_group6_validation"] = blueprint["group6_validation"]
    packet["practicality"]["minimum_concrete_steps"] = 5
    packet["practicality"]["reader_goal"] = (
        "读者能区分来源归属和系统选择，能解释一个组六单位与6个排列的关系，"
        "知道120是完整组六投注单位域而不是推荐清单，并能说明为什么全120单位不能作为本项目合规投注方案。"
    )
    packet["claims"]["allowed"].extend([
        "explain verified group6 mechanics and unordered bet-unit domain",
        "state exact deterministic group6 unit/outcome counts",
        "explain that 72% is a global structure share, not executable target-play coverage",
        "state that using all group6 units would be 100% target-play coverage and is blocked by the project coverage ceiling",
    ])
    return packet


def build_real_group6_article_prompt() -> str:
    packet = build_real_group6_article_packet()
    contract = packet["real_group6_validation"]
    permutations = "、".join(contract["example_permutations"])
    return build_generation_prompt(packet) + (
        "\n\n真实家族组六文章离线合同：\n"
        f"1. 正文必须逐字包含来源边界：{SOURCE_BOUNDARY}\n"
        f"2. 正文必须逐字包含域/覆盖率边界：{DOMAIN_BOUNDARY}\n"
        "3. 必须解释组六是三个数字互不相同；无序数字集合{1,2,3}是一个组六投注单位，"
        f"它覆盖六个有序排列：{permutations}。\n"
        "4. 必须解释完整组六域有120个无序单位，但禁止把120个单位逐项堆成投注清单。\n"
        "5. 必须用112说明两位相同一位不同属于组三，不属于组六；用777说明三同号既不是组六也不是组三。\n"
        "6. 必须清楚区分两个分母：720/1000=72%是全三位有序结果中的组六结构占比；"
        "120/120=100%才是把完整组六单位域全部使用时的目标玩法覆盖率。不得把72%写成低于90%所以可全投。\n"
        "7. 本篇只做玩法/域解释。不得输出 normalized_bets，不得给出“全120单位投注”或任何可执行全覆盖方案。\n"
        "8. practical_guidance 至少5步，并在 stop_condition 明确：解释到玩法域和示例核对后停止；若要给实际投注子集，"
        "必须另起合同，选取<=90%目标域并重新通过金额/经济参数门禁。\n"
        "9. 读者显示层继续优先使用‘分分彩’，不要在标题、SEO和普通正文把主题写成‘时时彩’。\n"
    )


def evaluate_real_group6_article(article: dict) -> RealGroup6ArticleQualityReport:
    content = str(article.get("content") or "")
    errors: list[str] = []
    score = 100

    for required in (SOURCE_BOUNDARY, DOMAIN_BOUNDARY):
        if required not in content:
            errors.append("required group6 provenance/compliance boundary missing or changed")
            score -= 25

    for marker in ("120", "720", "1000", "72%", "100%", "90%", "123", "132", "213", "231", "312", "321", "112", "777"):
        if marker not in content:
            errors.append(f"required group6 reproducibility marker missing: {marker}")
            score -= 4

    if not all(term in content for term in ("互不相同", "无序", "6个")):
        errors.append("group6 unit semantics are not explained clearly")
        score -= 15

    unsafe_phrases = (
        "72%低于90%所以可以全投",
        "72%低于90%，所以可以全投",
        "120个全部投注",
        "全120单位投注",
        "BRBCW-004115推荐组六",
        "来源推荐组六",
        "来源指定组六",
    )
    if any(phrase in content for phrase in unsafe_phrases):
        errors.append("article turns descriptive group6 domain into an unsafe executable/source claim")
        score -= 40

    if article.get("normalized_bets") is not None:
        errors.append("group6 validation article must not contain normalized_bets")
        score -= 40

    guidance = article.get("practical_guidance") or {}
    if len(guidance.get("steps") or []) < 5:
        errors.append("group6 article requires at least five practical explanation steps")
        score -= 10
    stop = str(guidance.get("stop_condition") or "")
    if "停止" not in stop or "90%" not in (stop + str(guidance.get("next_step_policy") or "")):
        errors.append("stop condition must block executable subset work until a separate <=90% contract exists")
        score -= 10

    if str(article.get("subject_lottery") or "分分彩") == "分分彩":
        for field in ("title", "seo_title", "meta_description", "primary_keyword"):
            if "时时彩" in str(article.get(field) or ""):
                errors.append(f"reader-facing group6 field uses legacy 时时彩 term: {field}")
                score -= 20

    if content.count("、") + content.count(",") > 180:
        errors.append("article appears to dump the full group6 unit list instead of explaining the domain")
        score -= 20

    return RealGroup6ArticleQualityReport(
        passed=(not errors and score >= 90),
        score=max(0, score),
        errors=list(dict.fromkeys(errors)),
    )
