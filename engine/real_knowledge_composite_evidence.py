from __future__ import annotations

from copy import deepcopy

from .real_knowledge_composite_article_contract import (
    CANDIDATE_INTEGRITY_BOUNDARY,
    ORDER_BOUNDARY,
    SOURCE_BOUNDARY,
)


class CompositeEvidenceError(ValueError):
    pass


def normalize_composite_claim_metadata(packet: dict, article: dict) -> dict:
    """Canonicalize only machine-owned evidence metadata; never rewrite content."""
    contract = packet.get("real_knowledge_composition") or {}
    if not contract:
        raise CompositeEvidenceError("real_knowledge_composition contract missing")
    entries = article.get("claim_evidence")
    if not isinstance(entries, list):
        raise CompositeEvidenceError("claim_evidence must be a list")

    normalized = deepcopy(article)
    rows = normalized["claim_evidence"]
    source_refs = list(packet.get("immutable_facts", {}).get("source_refs") or [])
    rule_refs = list(packet.get("immutable_facts", {}).get("rule_refs") or [])
    if len(source_refs) != 2 or not rule_refs:
        raise CompositeEvidenceError("locked source/rule refs are incomplete")

    canonical = [
        {
            "claim_text": "来源内容未独立验证；" + SOURCE_BOUNDARY,
            "claim_type": "source_claim",
            "support_type": "source_unverified",
            "support_refs": source_refs,
            "evidence_note": (
                "两份archive来源只支持各自方法原子的来源归属；组合、顺序和阈值由系统合同声明，"
                "不是来源事实，也不证明预测优势。"
            ),
        },
        {
            "claim_text": ORDER_BOUNDARY,
            "claim_type": "calculation",
            "support_type": "verified_rule",
            "support_refs": rule_refs,
            "evidence_note": (
                "系统分别执行冻结sum→span与反向span→sum的确定性候选空间枚举，"
                "证明中间路径760与690不同；此证据不证明预测优势。"
            ),
        },
        {
            "claim_text": CANDIDATE_INTEGRITY_BOUNDARY,
            "claim_type": "calculation",
            "support_type": "verified_rule",
            "support_refs": rule_refs,
            "evidence_note": (
                "系统对冻结后三000–999空间执行完整两层枚举，锁定534个最终候选并计算候选集合SHA256；"
                "hash只用于完整性校验。"
            ),
        },
    ]

    # Remove only exact duplicate model rows for the same locked statements so
    # an incorrectly classified duplicate cannot override canonical evidence.
    exact_texts = {SOURCE_BOUNDARY, "来源内容未独立验证；" + SOURCE_BOUNDARY, ORDER_BOUNDARY, CANDIDATE_INTEGRITY_BOUNDARY}
    rows[:] = [row for row in rows if not (isinstance(row, dict) and str(row.get("claim_text") or "") in exact_texts)]
    rows.extend(canonical)
    return normalized
