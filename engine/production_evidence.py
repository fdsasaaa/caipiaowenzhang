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
    """Repair only a narrow provider metadata mistake; never rewrite article content.

    Some providers occasionally classify a pure editorial scope/disclaimer sentence
    as source_unverified and attach BRBCW refs. That is not a source claim and then
    fails the intentionally strict source-qualification gate. This normalizer only
    converts those unmistakable editorial disclaimers to editorial + empty refs.

    Actual source claims, calculations, performance claims and any row containing
    source-attribution language remain untouched and must pass the normal gates.
    """
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


def generate_article_for_production(packet: dict, **kwargs) -> GenerationResult:
    """Run the standard generator, then normalize only production-safe metadata.

    This wrapper is intentionally used by the formal-production CLI rather than
    changing the generic generator used by research/smoke/group6 validation paths.
    """
    generated = generate_article(packet, **kwargs)
    normalized = normalize_production_claim_metadata(packet, generated.article)
    return GenerationResult(
        article=normalized,
        provider=generated.provider,
        model=generated.model,
        response_id=generated.response_id,
    )
