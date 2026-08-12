from __future__ import annotations

import re


_EDITORIAL_SCOPE_MARKERS = (
    "本文", "本篇", "这篇", "本次", "这里只", "只讲", "只说明", "仅说明",
)
_EDITORIAL_NEGATION_MARKERS = (
    "不讨论", "不涉及", "不提供", "不说明", "不引用", "不使用",
    "不用于", "不代表", "不能证明", "不等于", "未核验", "未经核验",
)
_SOURCE_ATTRIBUTION_MARKERS = (
    "来源提到", "来源声称", "原文提到", "原文声称", "资料提到", "文章提到",
    "来源认为", "原文认为", "据来源", "据原文",
)
_NUMERIC_FACT_RE = re.compile(r"\d|%|百分之|每注|元|\b倍\b")


def _is_pure_editorial_scope_disclaimer(text: str) -> bool:
    value = str(text or "").strip()
    if not value:
        return False
    if any(marker in value for marker in _SOURCE_ATTRIBUTION_MARKERS):
        return False
    if _NUMERIC_FACT_RE.search(value):
        return False
    return (
        any(marker in value for marker in _EDITORIAL_SCOPE_MARKERS)
        and any(marker in value for marker in _EDITORIAL_NEGATION_MARKERS)
    )


def normalize_generation_metadata(article: dict) -> dict:
    """Narrow deterministic cleanup for model metadata, never article prose.

    A model sometimes labels a pure scope/disclaimer sentence such as
    “本文不讨论未核验的平台经济参数” as `source_unverified` merely because
    source refs are present elsewhere in the packet. That sentence is editorial,
    not a source claim. Only that exact semantic class is normalized.

    Real source claims, numeric facts, calculations, performance/economics claims,
    and article prose are never rewritten here.
    """
    claims = article.get("claim_evidence")
    if not isinstance(claims, list):
        return article
    for row in claims:
        if not isinstance(row, dict):
            continue
        if row.get("claim_type") != "editorial":
            continue
        if row.get("support_type") != "source_unverified":
            continue
        if not _is_pure_editorial_scope_disclaimer(str(row.get("claim_text") or "")):
            continue
        row["support_type"] = "editorial"
        row["support_refs"] = []
        row["evidence_note"] = "编辑范围/风险说明，不是来源事实声明。"
    return article
