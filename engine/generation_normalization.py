from __future__ import annotations

import re

from .title_seo_runtime import apply_title_seo


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


def normalize_generation_metadata(article: dict, packet: dict | None = None) -> dict:
    """Normalize narrow evidence metadata, then perform post-body Title SEO selection.

    Article prose, immutable mechanics, rules, claims and calculations are not rewritten.
    The title layer runs only after the generated body already exists, produces 3-5
    candidates, and records the deterministic gate result for Approval.
    """
    claims = article.get("claim_evidence")
    if isinstance(claims, list):
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

    apply_title_seo(article, packet=packet)
    return article
