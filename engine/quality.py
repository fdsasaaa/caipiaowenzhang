from __future__ import annotations

from dataclasses import dataclass, field

from .dedup import duplicate_candidates
from .rules import verified_rules

PROMISE_WORDS = ("稳赚", "必中", "包赢", "必赚", "100%中奖", "百分百中奖", "无风险")


@dataclass
class QualityReport:
    passed: bool
    score: int
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def evaluate(article: dict) -> QualityReport:
    score = 100
    errors: list[str] = []
    warnings: list[str] = []
    content = article.get("content", "") or ""

    if not article.get("title") or not article.get("primary_keyword"):
        errors.append("missing title or primary_keyword")
        score -= 30
    if len(content.strip()) < 300:
        warnings.append("content is short (<300 chars)")
        score -= 10
    found = [w for w in PROMISE_WORDS if w in content or w in article.get("title", "")]
    if found:
        errors.append("guaranteed-outcome language: " + ", ".join(found))
        score -= 35
    provider_id = article.get("provider_id")
    if article.get("lottery") and article.get("play"):
        if not provider_id:
            errors.append("missing provider_id for rule-bound article")
            score -= 20
        elif not verified_rules(provider_id, article["lottery"], article["play"]):
            errors.append("no verified provider-aware rule for declared provider/lottery/play")
            score -= 35
    hits = duplicate_candidates(article)
    if hits:
        errors.append(f"duplicate risk: {hits[0].article_id} score={hits[0].score:.2f}")
        score -= 35
    if not article.get("rule_refs"):
        warnings.append("no rule_refs")
        score -= 5
    if not article.get("information_gain_type"):
        warnings.append("no information_gain_type")
        score -= 5
    return QualityReport(passed=(not errors and score >= 80), score=max(0, score), errors=errors, warnings=warnings)
