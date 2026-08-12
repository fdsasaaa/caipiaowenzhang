from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field

from .article_memory import get_article_record
from .draft_pipeline_v22 import build_multistage_draft_packet
from .filter_pipeline import final_pipeline_candidate_strings
from .knowledge_io import iter_brbcw_families
from .real_knowledge_multistage import build_real_knowledge_filter_pipeline


TARGET_ARTICLE_ID = "LCM-IDEA-bf5a9864b004ae17"
TARGET_FAMILY_ID = "FAM-32137acbb90340b9"
TARGET_RULE_REF = "SSC-HIST-MECH-LAST2-BSOE-V1"

SOURCE_PARAMETER_BOUNDARY = (
    "本例的“大小”和“单双”来自系统已登记的来源家族；“一大一小”和“一单一双”是系统在看演示样本前"
    "预先固定的研究参数，不是来源原文参数，也不代表预测优势。"
)


class RealKnowledgeLiveValidationError(ValueError):
    pass


@dataclass
class RealKnowledgeArticleReport:
    passed: bool
    score: int
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _family_for_record(record: dict) -> dict:
    family_id = str(record.get("technique_family") or "")
    family = next((row for row in iter_brbcw_families() if str(row.get("f") or "") == family_id), None)
    if family is None:
        raise RealKnowledgeLiveValidationError(f"family not found in static archive: {family_id}")

    article_atoms = list(record.get("technique_atoms") or [])
    archived_atoms = list(family.get("a") or [])
    if article_atoms != archived_atoms:
        raise RealKnowledgeLiveValidationError(
            f"registry/archive atom mismatch: registry={article_atoms!r} archive={archived_atoms!r}"
        )

    article_refs = set(record.get("source_refs") or [])
    family_refs = set(family.get("e") or [])
    if not article_refs or not article_refs.intersection(family_refs):
        raise RealKnowledgeLiveValidationError("registry source_refs do not intersect archived family provenance")
    return family


def build_real_knowledge_live_blueprint(article_id: str = TARGET_ARTICLE_ID) -> dict:
    """Freeze one existing source-backed article identity into a V2.2 validation blueprint.

    This is a validation-only revision target. It deliberately reuses the same
    article_id/SEO ownership so the approval layer can compare quality without
    creating a second article that competes for the same exact keyword.
    """
    record = get_article_record(article_id)
    if record is None:
        raise RealKnowledgeLiveValidationError(f"article not found in registry: {article_id}")
    if record.get("status") != "approved":
        raise RealKnowledgeLiveValidationError("real-knowledge live target must already be an approved registry identity")
    if article_id != TARGET_ARTICLE_ID:
        raise RealKnowledgeLiveValidationError("current live acceptance cycle is locked to exactly one article")
    if record.get("technique_family") != TARGET_FAMILY_ID:
        raise RealKnowledgeLiveValidationError("target technique family changed")
    if record.get("rule_refs") != [TARGET_RULE_REF]:
        raise RealKnowledgeLiveValidationError("target verified mechanics binding changed")

    family = _family_for_record(record)
    spec = build_real_knowledge_filter_pipeline(record)
    candidates = final_pipeline_candidate_strings(spec)
    if candidates != [
        "05", "07", "09", "16", "18", "25", "27", "29", "36", "38", "45", "47", "49",
        "50", "52", "54", "61", "63", "70", "72", "74", "81", "83", "90", "92", "94",
    ]:
        raise RealKnowledgeLiveValidationError("target final candidate list changed; refusing validation")

    primary = str(record.get("primary_keyword") or "")
    blueprint = {
        "blueprint_id": "BP-RK-V22-" + article_id.removeprefix("LCM-IDEA-"),
        "article_id": article_id,
        "provider_id": record.get("provider_id"),
        "lottery": record.get("lottery"),
        "play": record.get("play"),
        "subject_lottery": record.get("subject_lottery"),
        "subject_play": record.get("subject_play"),
        "content_type": record.get("content_type") or "technique_article",
        "site_category_key": record.get("site_category_key") or "tzjq",
        "technique_family": record.get("technique_family"),
        "technique_atoms": list(record.get("technique_atoms") or []),
        "resolved_selector": record.get("resolved_selector") or "后二",
        "selector_basis": record.get("selector_basis") or "verified_play",
        "source_positions": ["十位", "个位"],
        "angle_signature": "real-knowledge-v22-last2-bsoe-two-stage",
        "title": f"{primary}：100组后二号码按大小、单双两层筛到26组怎么复算",
        "slug_seed": record.get("slug") or "ffc-last2-bsoe-structure",
        "primary_keyword": primary,
        "secondary_keywords": list(record.get("secondary_keywords") or []),
        "search_intent": record.get("search_intent") or "学习具体投注技巧并看懂可复算案例",
        "information_gain_type": "source_backed_prefrozen_multistage_candidate_enumeration",
        "summary_goal": (
            "解释真实知识家族中的大小+单双两个方法原子，并严格区分来源原子与系统研究参数；"
            "从后二00–99共100个有序结果开始，按一大一小得到50个，再按一单一双得到26个，"
            "完整列出26个最终候选值和停止条件。"
        ),
        "outline": [
            "先说清来源支持什么、不支持什么",
            "后二为什么是00–99共100个有序结果",
            "第一层：一大一小如何从100个筛到50个",
            "第二层：一单一双如何从50个筛到26个",
            "最终26个候选值完整列出并说明如何复算",
            "演示样本只用于说明，不是真实开奖记录",
            "完成第二层后停止：新增条件必须下一次实验前单独冻结",
        ],
        "case_structure": record.get("case_structure") or "selector=后二;metrics=size_pattern,parity_pattern;scope=mechanics_only",
        "case_plan": {
            "supported": [
                {"atom": "big_small_filter", "metric": "big_count"},
                {"atom": "odd_even_filter", "metric": "odd_count"},
            ],
            "unsupported": [],
            "case_engine_ready": True,
            "resolved_selector": record.get("resolved_selector") or "后二",
            "selector_basis": record.get("selector_basis") or "verified_play",
            "source_position_supported": True,
        },
        "filter_pipeline_spec": spec,
        "case_scope": record.get("case_scope") or "mechanics_only",
        "rule_refs": list(record.get("rule_refs") or []),
        "source_refs": list(record.get("source_refs") or []),
        "source_support_count": int(family.get("n") or record.get("source_support_count") or 0),
        "source_risk_rate": float(family.get("r") or record.get("source_risk_rate") or 0.0),
        "fingerprint": record.get("fingerprint"),
        "status": "ready_for_draft",
        "blockers": [],
        "article_status": "validation_only_existing_identity",
        "editorial_contract_version": "1.1",
        "seo_requirements": {
            "plain_chinese": True,
            "example_required": True,
            "unique_information_gain_required": True,
            "reuse_existing_exact_keyword_owner": True,
            "avoid_keyword_stuffing": True,
            "avoid_guaranteed_outcomes": True,
        },
    }
    return blueprint


def build_real_knowledge_live_packet(article_id: str = TARGET_ARTICLE_ID) -> dict:
    blueprint = build_real_knowledge_live_blueprint(article_id)
    packet = build_multistage_draft_packet(blueprint)
    candidates = final_pipeline_candidate_strings(blueprint["filter_pipeline_spec"])
    final_line = f"最终{len(candidates)}个二位候选值：" + "、".join(candidates) + "。"
    packet = deepcopy(packet)
    packet["real_knowledge_validation"] = {
        "validation_only": True,
        "article_id": article_id,
        "technique_family": blueprint["technique_family"],
        "technique_atoms": list(blueprint["technique_atoms"]),
        "source_refs": list(blueprint["source_refs"]),
        "source_support_count": blueprint["source_support_count"],
        "source_risk_rate": blueprint["source_risk_rate"],
        "parameter_policy": blueprint["filter_pipeline_spec"]["parameter_policy"],
        "required_source_parameter_boundary": SOURCE_PARAMETER_BOUNDARY,
        "final_candidates": candidates,
        "required_final_candidate_line": final_line,
        "must_list_every_final_candidate": True,
        "must_not_claim_prediction_advantage": True,
        "registry_write": False,
        "website_write": False,
        "scheduled": False,
        "published": False,
    }
    packet["practicality"]["reader_goal"] = (
        "读者能说清来源只提供方法原子，参数由系统预冻结；并能从00–99的100个有序结果"
        "按100→50→26逐层复算，最后核对完整26个候选值后停止。"
    )
    return packet


def normalize_real_knowledge_article(packet: dict, article: dict) -> dict:
    """Add only canonical evidence rows for system-owned exact validation facts.

    Content is never repaired here. If the model omits the required provenance
    boundary or candidate list, the quality gate must fail rather than silently
    inserting prose.
    """
    contract = packet.get("real_knowledge_validation") or {}
    if not contract:
        raise RealKnowledgeLiveValidationError("real_knowledge_validation contract missing")
    normalized = deepcopy(article)
    entries = normalized.setdefault("claim_evidence", [])
    if not isinstance(entries, list):
        raise RealKnowledgeLiveValidationError("claim_evidence must be a list")

    rows = [
        {
            "claim_text": contract["required_source_parameter_boundary"],
            "claim_type": "source_claim",
            "support_type": "source_unverified",
            "support_refs": list(contract["source_refs"]),
            "evidence_note": (
                "来源引用只支持方法家族中登记了大小/单双原子；具体count参数来自系统预冻结研究参数，"
                "不由来源证明，也不证明预测优势。"
            ),
        },
        {
            "claim_text": contract["required_final_candidate_line"],
            "claim_type": "calculation",
            "support_type": "verified_rule",
            "support_refs": list(packet.get("immutable_facts", {}).get("rule_refs") or []),
            "evidence_note": (
                "系统对00–99有序后二空间按Draft Packet冻结的big_count=1与odd_count=1逐项枚举；"
                "该列表只证明筛选结果，不代表未来命中优势。"
            ),
        },
    ]
    existing = {
        (str(row.get("claim_text") or ""), str(row.get("support_type") or ""), tuple(row.get("support_refs") or []))
        for row in entries if isinstance(row, dict)
    }
    for row in rows:
        key = (row["claim_text"], row["support_type"], tuple(row["support_refs"]))
        if key not in existing:
            entries.append(row)
            existing.add(key)
    return normalized


def evaluate_real_knowledge_article(packet: dict, article: dict) -> RealKnowledgeArticleReport:
    contract = packet.get("real_knowledge_validation") or {}
    if not contract:
        return RealKnowledgeArticleReport(False, 0, errors=["real_knowledge_validation contract missing"])

    content = str(article.get("content") or "")
    errors: list[str] = []
    warnings: list[str] = []
    score = 100

    boundary = str(contract.get("required_source_parameter_boundary") or "")
    if not boundary or boundary not in content:
        errors.append("source/parameter provenance boundary sentence missing or changed")
        score -= 30

    candidate_line = str(contract.get("required_final_candidate_line") or "")
    if not candidate_line or candidate_line not in content:
        errors.append("complete final 26-candidate line missing or changed")
        score -= 30

    candidates = list(contract.get("final_candidates") or [])
    if len(candidates) != 26:
        errors.append("frozen final candidate list no longer has 26 values")
        score -= 20

    result = packet.get("practicality", {}).get("filter_pipeline_result") or {}
    if result.get("starting_space") != 100 or result.get("final_space") != 26 or result.get("total_excluded") != 74:
        errors.append("real-family aggregate pipeline changed from 100 -> 26 / excluded 74")
        score -= 20
    stages = result.get("stages") or []
    if [stage.get("after_space") for stage in stages] != [50, 26]:
        errors.append("real-family stage contraction changed from 100 -> 50 -> 26")
        score -= 20
    if [stage.get("excluded_space") for stage in stages] != [50, 24]:
        errors.append("real-family stage exclusions changed from 50 then 24")
        score -= 20

    for phrase in ("一大一小", "一单一双", "100", "50", "26", "74"):
        if phrase not in content:
            errors.append(f"required reproducibility marker missing from content: {phrase}")
            score -= 8

    guidance = article.get("practical_guidance") or {}
    if len(guidance.get("steps") or []) < 5:
        errors.append("real-knowledge article requires at least five concrete practical steps")
        score -= 10

    if contract.get("registry_write") is not False or contract.get("website_write") is not False:
        errors.append("validation contract unexpectedly enables write path")
        score -= 50
    if contract.get("scheduled") is not False or contract.get("published") is not False:
        errors.append("validation contract unexpectedly enables publishing path")
        score -= 50

    passed = not errors and score >= 90
    return RealKnowledgeArticleReport(
        passed=passed,
        score=max(0, score),
        errors=list(dict.fromkeys(errors)),
        warnings=list(dict.fromkeys(warnings)),
    )
