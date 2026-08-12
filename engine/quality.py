from __future__ import annotations

import re
from dataclasses import dataclass, field

from .compliance import validate_portfolio
from .dedup import duplicate_candidates
from .rules import load_rules, rule_capability
from .semantic_dedup import structural_duplicate_candidates

PROMISE_WORDS = ("稳赚", "必中", "包赢", "必赚", "100%中奖", "百分百中奖", "无风险")


@dataclass
class QualityReport:
    passed: bool
    score: int
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _verified_mechanics_from_explicit_refs(article: dict) -> list[str]:
    """Resolve mechanics from immutable rule_refs without conflating display lottery names.

    Public articles may use subject_lottery=分分彩 while the verified historical
    mechanics taxonomy remains 时时彩. An explicit verified mechanics rule_ref is
    stronger evidence than requiring the reader-facing lottery label to equal the
    rule archive's historical taxonomy label.
    """
    refs = {str(value) for value in (article.get("rule_refs") or []) if value}
    play = str(article.get("play") or "").strip()
    if not refs or not play:
        return []
    matched: list[str] = []
    for rule in load_rules():
        if rule.get("rule_id") not in refs:
            continue
        if rule.get("status") != "verified" or rule.get("scope", "full") not in {"mechanics", "full"}:
            continue
        if play != rule.get("play") and play not in (rule.get("aliases") or []):
            continue
        matched.append(str(rule.get("rule_id")))
    return matched


def _public_terminology_review(article: dict) -> tuple[list[str], list[str], int]:
    """Prefer 分分时时彩 in reader-facing copy while preserving internal/source provenance.

    This is intentionally not a blind global replacement: historical rule names,
    source provenance and archive metadata may still legitimately contain 时时彩.
    """
    errors: list[str] = []
    warnings: list[str] = []
    penalty = 0
    if str(article.get("subject_lottery") or "") != "分分彩":
        return errors, warnings, penalty

    strict_fields = {
        "title": str(article.get("title") or ""),
        "seo_title": str(article.get("seo_title") or ""),
        "meta_description": str(article.get("meta_description") or ""),
        "primary_keyword": str(article.get("primary_keyword") or ""),
    }
    bad = [name for name, value in strict_fields.items() if "时时彩" in value]
    if bad:
        errors.append("reader-facing FFC article uses legacy 时时彩 term in: " + ", ".join(bad))
        penalty += 20

    content = str(article.get("content") or "")
    if "时时彩" in content:
        plain = re.sub(r"<[^>]+>", "。", content)
        legacy_sentences = [
            sentence.strip()
            for sentence in re.split(r"[。！？!?]+", plain)
            if "时时彩" in sentence
        ]
        qualified_markers = ("历史", "规则库", "规则名", "内部", "来源原文", "原文术语", "归档", "mechanics")
        unqualified = [
            sentence for sentence in legacy_sentences
            if not any(marker in sentence for marker in qualified_markers)
        ]
        if unqualified:
            warnings.append(
                "reader-facing FFC content should replace legacy 时时彩 with 分分时时彩 unless explicitly discussing historical/source terminology"
            )
            penalty += 5
    return errors, warnings, penalty


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

    terminology_errors, terminology_warnings, terminology_penalty = _public_terminology_review(article)
    errors.extend(terminology_errors)
    warnings.extend(terminology_warnings)
    score -= terminology_penalty

    if article.get("lottery") and article.get("play"):
        case_scope = article.get("case_scope", "mechanics_only")
        cap = rule_capability(article.get("provider_id"), article["lottery"], article["play"])
        explicit_mechanics = _verified_mechanics_from_explicit_refs(article)
        mechanics_verified = bool(cap["mechanics_verified"] or explicit_mechanics)
        if not mechanics_verified:
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

    structural_hits = structural_duplicate_candidates(article)
    if structural_hits:
        hit = structural_hits[0]
        errors.append(
            f"structural duplicate risk: {hit.article_id} score={hit.score:.2f} reasons={','.join(hit.reasons)}"
        )
        score -= 40

    if not article.get("rule_refs"):
        warnings.append("no rule_refs")
        score -= 5
    if not article.get("information_gain_type"):
        warnings.append("no information_gain_type")
        score -= 5
    return QualityReport(passed=(not errors and score >= 80), score=max(0, score), errors=errors, warnings=warnings)
