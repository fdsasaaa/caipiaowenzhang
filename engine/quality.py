from __future__ import annotations

from dataclasses import dataclass, field

from .compliance import validate_portfolio
from .dedup import duplicate_candidates
from .rules import rule_capability

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

    if article.get("lottery") and article.get("play"):
        case_scope = article.get("case_scope", "mechanics_only")
        cap = rule_capability(article.get("provider_id"), article["lottery"], article["play"])
        if not cap["mechanics_verified"]:
            errors.append("no verified gameplay mechanics for declared lottery/play")
            score -= 35
        if case_scope == "economics":
            if not article.get("provider_id"):
                errors.append("economics case requires provider_id")
                score -= 20
            elif not cap["economics_verified"]:
                errors.append("no verified provider economics for stake/payout/rebate case")
                score -= 35
        elif not cap["economics_verified"]:
            warnings.append("provider economics unverified: do not state stake/payout/rebate as fact")

    normalized_bets = article.get("normalized_bets")
    if normalized_bets is not None:
        if not isinstance(normalized_bets, list):
            errors.append("normalized_bets must be a list")
            score -= 35
        else:
            compliance = validate_portfolio(normalized_bets)
            if not compliance.passed:
                codes = sorted({v.get("code", "unknown") for v in compliance.violations})
                errors.append("bet compliance failed: " + ", ".join(codes))
                score -= 40

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
