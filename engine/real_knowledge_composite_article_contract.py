from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product

from .ai_generation_v22 import build_multistage_generation_prompt
from .draft_pipeline_v22 import build_multistage_draft_packet
from .filter_pipeline import final_pipeline_candidate_strings
from .real_knowledge_composition import (
    BINDING_BASIS,
    COMPOSITION_BASIS,
    COMPOSITION_ID,
    EXPECTED_CANDIDATE_SHA256,
    PARAMETER_POLICY,
    RULE_REF,
    SPAN_FAMILY,
    SUM_FAMILY,
    build_sum_span_composite_evidence,
)


ARTICLE_ID = "VAL-RK-COMP-LAST3-SUM-SPAN-V1"
PRIMARY_KEYWORD = "分分彩后三和值跨度技巧"
SOURCE_BOUNDARY = (
    "本例有两个独立来源家族：BRBCW-006020只支持和值方法原子的来源归属，"
    "BRBCW-002590只支持跨度方法原子的来源归属；把两者组合、先和值后跨度、"
    "以及使用和值8–19和跨度3–7，都是系统在看演示样本前预先冻结的研究设计，"
    "不是任一来源原文给出的组合方法，也不代表预测优势。"
)
ORDER_BOUNDARY = (
    "本实验冻结顺序是先和值、后跨度；即使反过来最终候选集合可能相同，"
    "中间路径会从1000→760→534变成1000→690→534，所以不能事后互换顺序再当成同一个实验。"
)
CANDIDATE_INTEGRITY_BOUNDARY = (
    f"机器验收锁定最终候选数为534，候选集合SHA256为{EXPECTED_CANDIDATE_SHA256}；"
    "正文不需要堆满534个号码，读者复算看条件和示例，完整集合由机器枚举与哈希保证一致。"
)


class CompositeArticleContractError(ValueError):
    pass


@dataclass
class CompositeArticleQualityReport:
    passed: bool
    score: int
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _all_three_digit_strings() -> list[str]:
    return ["".join(str(d) for d in values) for values in product(range(10), repeat=3)]


def _spot_checks() -> dict:
    evidence = build_sum_span_composite_evidence()
    included = final_pipeline_candidate_strings(evidence["pipeline_spec"])
    included_set = set(included)
    excluded = [value for value in _all_three_digit_strings() if value not in included_set]
    # Stable examples spread across the ordered domain instead of cherry-picking
    # from one edge only. They are explanatory checks, never performance data.
    included_indexes = (0, 53, 106, 267, 400, 533)
    excluded_indexes = (0, 46, 93, 232, 349, 465)
    return {
        "included": [included[i] for i in included_indexes],
        "excluded": [excluded[i] for i in excluded_indexes],
    }


def build_composite_article_blueprint() -> dict:
    evidence = build_sum_span_composite_evidence()
    checks = _spot_checks()
    spec = evidence["pipeline_spec"]
    return {
        "blueprint_id": "BP-" + ARTICLE_ID,
        "article_id": ARTICLE_ID,
        "provider_id": "research-validation-only",
        "lottery": "分分彩",
        "play": "后三直选",
        "subject_lottery": "分分彩",
        "subject_play": "后三直选",
        "content_type": "technique_article",
        "site_category_key": "tzjq",
        "technique_family": COMPOSITION_ID,
        "technique_atoms": ["sum_range", "span_range"],
        "resolved_selector": "后三",
        "selector_basis": "verified_play",
        "source_positions": ["百位", "十位", "个位"],
        "angle_signature": "real-knowledge-cross-family-last3-sum-span",
        "title": "分分彩后三和值跨度技巧：1000组号码按和值、跨度两层筛到534组怎么复算",
        "slug_seed": "ffc-last3-sum-span-two-source-composite",
        "primary_keyword": PRIMARY_KEYWORD,
        "secondary_keywords": ["分分彩后三技巧", "后三和值", "后三跨度", "彩票技巧复算"],
        "search_intent": "学习和值与跨度两层筛选如何按固定顺序复算，并看懂来源边界",
        "information_gain_type": "cross_family_source_provenance_plus_deterministic_multistage_reproduction",
        "summary_goal": (
            "清楚区分两个真实来源家族各自支持的单一方法原子与系统自行设计的组合；"
            "从后三000–999共1000个有序结果开始，按和值8–19得到760个，再按跨度3–7得到534个，"
            "解释每层排除数、顺序冻结原因和可人工核对的入选/排除示例。"
        ),
        "outline": [
            "先拆开两份来源：和值来源只支持和值原子，跨度来源只支持跨度原子",
            "为什么后三直选是000–999共1000个有序结果",
            "系统为什么把组合顺序冻结为先和值后跨度",
            "第一层和值8–19：1000→760，排除240",
            "第二层跨度3–7：760→534，再排除226",
            "用固定入选与排除示例演示如何手工复算",
            "为什么正文不堆534个号码：机器count/hash锁全集，正文负责解释方法",
            "演示样本不是历史开奖，完成第二层后停止",
        ],
        "case_structure": "selector=后三;metrics=sum_range,span_range;scope=mechanics_only;composition=system_authored",
        "case_plan": {
            "supported": [
                {"atom": "sum_range", "source_family": SUM_FAMILY["family_id"], "source_ref": SUM_FAMILY["source_ref"]},
                {"atom": "span_range", "source_family": SPAN_FAMILY["family_id"], "source_ref": SPAN_FAMILY["source_ref"]},
            ],
            "unsupported": [],
            "case_engine_ready": True,
            "resolved_selector": "后三",
            "selector_basis": "verified_play",
            "source_position_supported": True,
        },
        "filter_pipeline_spec": spec,
        "case_scope": "mechanics_only",
        "rule_refs": [RULE_REF],
        "source_refs": [SUM_FAMILY["source_ref"], SPAN_FAMILY["source_ref"]],
        "source_support_count": SUM_FAMILY["source_support_count"] + SPAN_FAMILY["source_support_count"],
        "source_risk_rate": max(SUM_FAMILY["source_risk_rate"], SPAN_FAMILY["source_risk_rate"]),
        "fingerprint": "rk-comp-last3-sum-span-v1",
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
        "composition_contract": {
            "composition_id": COMPOSITION_ID,
            "binding_basis": BINDING_BASIS,
            "composition_basis": COMPOSITION_BASIS,
            "parameter_policy": PARAMETER_POLICY,
            "source_boundary": SOURCE_BOUNDARY,
            "order_boundary": ORDER_BOUNDARY,
            "candidate_integrity_boundary": CANDIDATE_INTEGRITY_BOUNDARY,
            "final_candidate_count": evidence["final_candidate_count"],
            "final_candidate_sha256": evidence["final_candidate_sha256"],
            "spot_checks": checks,
            "must_list_all_final_candidates": False,
            "must_explain_how_to_test_any_candidate": True,
        },
    }


def build_composite_article_packet() -> dict:
    blueprint = build_composite_article_blueprint()
    packet = build_multistage_draft_packet(blueprint)
    contract = blueprint["composition_contract"]
    packet["real_knowledge_composition"] = contract
    packet["practicality"]["minimum_concrete_steps"] = 6
    packet["practicality"]["reader_goal"] = (
        "读者能区分两份来源各自支持什么，能按固定的和值→跨度顺序从1000复算到760再到534，"
        "能拿任意一个三位数检查和值与跨度是否满足条件，并知道第二层后必须停止。"
    )
    packet["claims"]["allowed"].extend([
        "state exact machine-enumerated stage counts from the frozen cross-family composition",
        "explain that the cross-family composition/order/parameters are system-authored research choices",
        "show deterministic included/excluded spot-check candidates",
    ])
    return packet


def build_composite_article_prompt() -> str:
    packet = build_composite_article_packet()
    contract = packet["real_knowledge_composition"]
    included = "、".join(contract["spot_checks"]["included"])
    excluded = "、".join(contract["spot_checks"]["excluded"])
    return build_multistage_generation_prompt(packet) + (
        "\n\n跨真实来源家族文章合同（离线预检版本）：\n"
        f"1. 正文必须逐字包含来源边界：{SOURCE_BOUNDARY}\n"
        f"2. 正文必须逐字包含顺序边界：{ORDER_BOUNDARY}\n"
        "3. 必须写清后三直选是000–999共1000个有序结果；第一层和值8–19得到760个、排除240个；"
        "第二层跨度3–7从760个得到534个、排除226个；总排除466个。\n"
        f"4. 正文必须逐字包含候选完整性说明：{CANDIDATE_INTEGRITY_BOUNDARY}\n"
        f"5. 固定入选核对示例：{included}。固定排除核对示例：{excluded}。"
        "每个示例至少挑2个写出具体和值与跨度计算，说明为什么进或为什么出。\n"
        "6. 不要求把534个候选全部塞进正文；禁止用大段号码清单代替解释。"
        "必须告诉读者如何对任意三位数自行计算和值=sum(三位数字)，跨度=max-min，再按两层条件核对。\n"
        "7. 两个source_ref各自只能支持自己的方法原子。不得写‘来源推荐和值+跨度组合’、"
        "‘来源规定先和值后跨度’或‘来源证明8–19/3–7更好’。\n"
        "8. 必须保留‘不是真实开奖记录’语义披露；任何演示样本只负责解释计算，不参与参数选择。\n"
        "9. 第二层完成后停止。任何第三层都必须在新的实验合同里先绑定来源/规则并预冻结。\n"
        "10. 不得把从1000缩到534写成命中率提高、胜率提高、盈利能力提高或推荐号码。"
    )


def evaluate_composite_article_content(article: dict) -> CompositeArticleQualityReport:
    packet = build_composite_article_packet()
    contract = packet["real_knowledge_composition"]
    content = str(article.get("content") or "")
    errors: list[str] = []
    score = 100

    required_exact = [SOURCE_BOUNDARY, ORDER_BOUNDARY, CANDIDATE_INTEGRITY_BOUNDARY]
    for sentence in required_exact:
        if sentence not in content:
            errors.append("required composite provenance/integrity sentence missing or changed")
            score -= 20

    for marker in ("1000", "760", "534", "240", "226", "466", "和值8–19", "跨度3–7"):
        if marker not in content:
            errors.append(f"required composite reproducibility marker missing: {marker}")
            score -= 8

    # Require spot-check visibility without requiring the full 534-set dump.
    for value in contract["spot_checks"]["included"][:3] + contract["spot_checks"]["excluded"][:3]:
        if value not in content:
            errors.append(f"required deterministic spot-check candidate missing: {value}")
            score -= 4

    if "和值" not in content or "跨度" not in content or not any(term in content for term in ("最大值减最小值", "max-min", "最大减最小")):
        errors.append("reader-facing candidate test formula is incomplete")
        score -= 15

    if any(term in content for term in ("来源推荐和值+跨度", "来源规定先和值后跨度", "来源证明8–19/3–7更好")):
        errors.append("composition/order/parameters were falsely attributed to sources")
        score -= 40

    guidance = article.get("practical_guidance") or {}
    if len(guidance.get("steps") or []) < 6:
        errors.append("composite article requires at least six practical steps")
        score -= 10
    if "第二层" not in str(guidance.get("stop_condition") or ""):
        errors.append("stop condition must explicitly stop after stage two")
        score -= 10

    # A giant candidate dump is not a quality virtue here. More than 180
    # comma-like separators strongly suggests the explanation was replaced by a list.
    list_separators = content.count("、") + content.count(",")
    if list_separators > 180:
        errors.append("content appears to dump a large candidate list instead of explaining the method")
        score -= 20

    passed = not errors and score >= 90
    return CompositeArticleQualityReport(passed=passed, score=max(0, score), errors=list(dict.fromkeys(errors)))
