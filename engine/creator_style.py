from __future__ import annotations

import re
from dataclasses import dataclass, field

ENGINE_JARGON = (
    "Draft Packet", "Blueprint", "angle_delivery", "claim_evidence", "support_type",
    "provider_response_id", "candidate_capacity", "article_angle_contract", "system_research",
    "机器合同", "工程合同", "候选容量",
)
TEMPLATE_PHRASES = (
    "本文将", "本篇将", "下面将", "综上所述", "通过以上分析可以看出", "总的来说",
)


@dataclass
class CreatorStyleReport:
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def evaluate_creator_style(article: dict) -> CreatorStyleReport:
    content = str(article.get("content") or "")
    title = str(article.get("title") or "")
    errors: list[str] = []
    warnings: list[str] = []

    leaked = [term for term in ENGINE_JARGON if term in content or term in title]
    if leaked:
        errors.append("reader-facing article leaks internal engineering language: " + ", ".join(leaked[:4]))

    template_hits = sum(content.count(term) for term in TEMPLATE_PHRASES)
    if template_hits >= 4:
        errors.append("article reads like a repeated batch template rather than natural human writing")
    elif template_hits >= 2:
        warnings.append("article uses several generic template phrases; simplify the prose")

    heading_count = len(re.findall(r"<h[23]\b", content, flags=re.IGNORECASE))
    if heading_count > 8:
        warnings.append("article has many sections; consider a shorter, more human structure")

    plain = re.sub(r"<[^>]+>", "", content)
    if len(plain) > 4000:
        warnings.append("article is long for creator-first concise style")

    return CreatorStyleReport(passed=not errors, errors=errors, warnings=warnings)
