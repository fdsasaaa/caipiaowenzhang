from __future__ import annotations

from copy import deepcopy

from .ai_generation import GenerationResult, generate_article

_SOURCE_MARKERS = ("来源", "原文", "资料", "BRBCW-", "source")
_DISCLAIMER_MARKERS = (
    "不讨论未核验的平台经济参数",
    "不涉及未核验的平台经济参数",
    "不提供未核验的平台经济参数",
    "本文只讲",
)


def _pure_editorial_disclaimer(row: dict) -> bool:
    if str(row.get("claim_type") or "") != "editorial":
        return False
    if str(row.get("support_type") or "") != "source_unverified":
        return False
    claim = str(row.get("claim_text") or "").strip()
    if not claim:
        return False
    if any(marker in claim for marker in _SOURCE_MARKERS):
        return False
    if not any(marker in claim for marker in _DISCLAIMER_MARKERS):
        return False
    if any(marker in claim for marker in (
        "命中率", "胜率", "成功率", "准确率", "下一期会", "一定会出", "肯定会出",
        "赔率为", "返点为", "奖金为", "收益率", "利润率", "盈利率",
    )):
        return False
    return True


def normalize_production_claim_metadata(packet: dict, article: dict) -> dict:
    """Repair only a narrow provider metadata mistake; never rewrite article content."""
    normalized = deepcopy(article)
    entries = normalized.get("claim_evidence")
    if not isinstance(entries, list):
        return normalized
    for row in entries:
        if not isinstance(row, dict) or not _pure_editorial_disclaimer(row):
            continue
        row["support_type"] = "editorial"
        row["support_refs"] = []
        note = str(row.get("evidence_note") or "").strip()
        suffix = "system normalized pure editorial disclaimer; no source evidence asserted"
        row["evidence_note"] = f"{note}; {suffix}" if note else suffix
    return normalized


def _packet_with_production_source_boundaries(packet: dict) -> dict:
    generation_packet = deepcopy(packet)
    spec = (generation_packet.get("practicality") or {}).get("primary_filter_spec")
    if not isinstance(spec, dict) or spec.get("basis") != "system_research_prefrozen":
        return generation_packet

    source_use = generation_packet.setdefault("source_use", {})
    source_use["primary_filter_parameter_owner"] = "system_research"
    source_use["primary_filter_parameter_source_attribution_allowed"] = False
    source_use["primary_filter_parameter_instruction"] = (
        "具体主筛选参数由系统在查看演示样本前预先冻结。BRBCW/source_refs只支持 broad 技巧原子的来源归属；"
        "不得写成来源推荐、来源指定或原文给出的具体参数。若正文讨论来源，只能明确写成来源提到 broad 方法且尚未独立验证。"
    )
    generation_packet.setdefault("claims", {}).setdefault("allowed", []).append(
        "state the concrete primary-filter parameter as a system-prefrozen research choice, never as a source-selected parameter"
    )
    return generation_packet


def generate_article_for_production(packet: dict, **kwargs) -> GenerationResult:
    """Run the standard generator with production-only source boundaries.

    Generic research/smoke/group6 generators are untouched. After generation,
    only unmistakable pure-editorial disclaimer metadata may be normalized; article
    content and actual source/performance claims remain unchanged and fail closed.
    """
    generation_packet = _packet_with_production_source_boundaries(packet)
    generated = generate_article(generation_packet, **kwargs)
    normalized = normalize_production_claim_metadata(packet, generated.article)
    return GenerationResult(
        article=normalized,
        provider=generated.provider,
        model=generated.model,
        response_id=generated.response_id,
    )
