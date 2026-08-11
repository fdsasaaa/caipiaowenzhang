from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field

from .analysis_metrics import POSITION_INDEX, WINDOW_INDEXES
from .blueprints import generate_blueprints
from .casebook import descriptive_case, frequency_case, omission_case

GUARANTEE_TERMS = ["稳赚", "必中", "包赢", "必赚", "百分百中奖", "100%中奖", "无风险"]


@dataclass
class DraftReview:
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _seed_from_blueprint(blueprint: dict) -> int:
    raw = blueprint.get("fingerprint") or blueprint.get("blueprint_id") or blueprint.get("article_id") or "default"
    return int(hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16], 16)


def synthetic_draws(blueprint: dict, count: int = 16) -> list[str]:
    """Deterministic five-digit illustrative draws. Never present as historical data."""
    rng = random.Random(_seed_from_blueprint(blueprint))
    return ["".join(str(rng.randrange(10)) for _ in range(5)) for _ in range(count)]


def _selector(blueprint: dict) -> str:
    case_structure = blueprint.get("case_structure", "")
    if "selector=" in case_structure:
        value = case_structure.split("selector=", 1)[1].split(";", 1)[0].split("/", 1)[0]
        if value in WINDOW_INDEXES or value in POSITION_INDEX:
            return value
    play = blueprint.get("play", "")
    for value in ("前二", "后二", "前三", "中三", "后三", "前四", "后四", "五星", "万位", "千位", "百位", "十位", "个位"):
        if value in play:
            return value
    return "五星"


def build_case_bundle(blueprint: dict) -> dict:
    draws = synthetic_draws(blueprint)
    selector = _selector(blueprint)
    atoms = set(blueprint.get("technique_atoms", []))
    bundle = {
        "case_type": "synthetic_validation",
        "must_label_as": "演示数据，不是真实开奖记录",
        "draws": draws,
        "selector": selector,
        "descriptive": descriptive_case(draws, selector, min(12, len(draws))),
    }
    if "omission_threshold" in atoms and selector in POSITION_INDEX:
        bundle["omission"] = omission_case(draws, selector, threshold=2, lookback=min(12, len(draws)))
    if atoms.intersection({"cold_hot_split", "frequency_window"}):
        bundle["frequency"] = frequency_case(draws, selector, lookback=min(12, len(draws)), hot_top_n=3)
    return bundle


def _meta_description(blueprint: dict) -> str:
    lottery = blueprint.get("lottery", "彩票")
    play = blueprint.get("play", "玩法")
    primary = blueprint.get("primary_keyword", f"{lottery}{play}技巧")
    return f"{primary}案例讲解：先说明{play}规则，再用可复算演示数据展示筛选步骤、注数检查和常见误区，不把历史统计包装成必中结论。"


def build_draft_packet(blueprint: dict) -> dict:
    if blueprint.get("status") != "ready_for_draft":
        raise ValueError(f"blueprint is not ready_for_draft: {blueprint.get('status')}")
    if not blueprint.get("rule_refs"):
        raise ValueError("draft packet requires rule_refs")
    case_bundle = build_case_bundle(blueprint)
    economics_allowed = blueprint.get("case_scope") == "economics"
    packet_id = "DP-" + (blueprint.get("fingerprint") or hashlib.sha256(str(blueprint).encode()).hexdigest())[:16]
    return {
        "packet_id": packet_id,
        "article_id": blueprint["article_id"],
        "blueprint_id": blueprint["blueprint_id"],
        "status": "ready_for_ai_draft",
        "immutable_facts": {
            "provider_id": blueprint.get("provider_id"),
            "lottery": blueprint.get("lottery"),
            "play": blueprint.get("play"),
            "technique_family": blueprint.get("technique_family"),
            "technique_atoms": blueprint.get("technique_atoms", []),
            "rule_refs": blueprint.get("rule_refs", []),
            "source_refs": blueprint.get("source_refs", []),
            "case_scope": blueprint.get("case_scope"),
            "fingerprint": blueprint.get("fingerprint"),
            "case_structure": blueprint.get("case_structure"),
            "information_gain_type": blueprint.get("information_gain_type"),
        },
        "seo": {
            "title": blueprint.get("title"),
            "slug_seed": blueprint.get("slug_seed"),
            "primary_keyword": blueprint.get("primary_keyword"),
            "secondary_keywords": blueprint.get("secondary_keywords", []),
            "search_intent": blueprint.get("search_intent"),
            "meta_description": _meta_description(blueprint),
        },
        "style": {
            "language": "zh-CN",
            "plain_chinese": True,
            "short_paragraphs": True,
            "avoid_empty_intro": True,
            "explain_with_example": True,
            "tone": "clear_practical_research",
        },
        "outline": blueprint.get("outline", []),
        "case_bundle": case_bundle,
        "claims": {
            "allowed": [
                "explain verified gameplay mechanics",
                "describe the supplied synthetic case exactly as an illustration",
                "explain calculation steps and limitations",
                "state that frequency/omission/sum/span are descriptive unless separately validated",
            ],
            "forbidden_terms": GUARANTEE_TERMS,
            "economics_allowed": economics_allowed,
            "unverified_hit_rate_as_fact": False,
            "historical_pattern_as_future_guarantee": False,
        },
        "compliance": {
            "policy_ref": "USER-BET-COMPLIANCE-90-V1",
            "normalized_bets_required_for_executable_bet_examples": True,
            "export_requires_pass": True,
        },
        "source_use": {
            "paraphrase_required": True,
            "copy_source_article_verbatim": False,
            "source_claims_must_remain_unverified_unless_rule_refs_support_them": True,
        },
        "output_contract": {
            "required_fields": ["article_id", "title", "slug", "meta_description", "primary_keyword", "search_intent", "summary", "content", "rule_refs", "case_scope", "status"],
            "status_after_generation": "draft",
            "must_include_case_label": case_bundle["must_label_as"],
        },
    }


def generate_draft_packets(provider_id: str, lottery: str, play: str, count: int = 10) -> dict:
    blueprint_result = generate_blueprints(provider_id, lottery, play, max(count * 2, count))
    packets = []
    skipped = []
    for blueprint in blueprint_result.get("blueprints", []):
        if blueprint.get("status") != "ready_for_draft":
            skipped.append({"blueprint_id": blueprint.get("blueprint_id"), "status": blueprint.get("status"), "blockers": blueprint.get("blockers", [])})
            continue
        try:
            packets.append(build_draft_packet(blueprint))
        except ValueError as exc:
            skipped.append({"blueprint_id": blueprint.get("blueprint_id"), "status": "packet_blocked", "reason": str(exc)})
        if len(packets) >= count:
            break
    return {
        "provider_id": provider_id,
        "lottery": lottery,
        "play": play,
        "requested": count,
        "generated": len(packets),
        "skipped": skipped,
        "packets": packets,
    }


def review_draft(packet: dict, article: dict) -> DraftReview:
    errors: list[str] = []
    warnings: list[str] = []
    content = article.get("content", "") or ""
    title = article.get("title", "") or ""
    seo = packet.get("seo", {})
    required = packet.get("output_contract", {}).get("required_fields", [])
    missing = [field for field in required if not article.get(field)]
    if missing:
        errors.append("missing required fields: " + ", ".join(missing))
    primary = seo.get("primary_keyword", "")
    if primary and primary not in title and primary not in content[:400]:
        warnings.append("primary keyword not present in title or early content")
    for term in packet.get("claims", {}).get("forbidden_terms", []):
        if term in title or term in content:
            errors.append(f"forbidden guaranteed-outcome term: {term}")
    label = packet.get("output_contract", {}).get("must_include_case_label")
    if label and label not in content:
        errors.append("synthetic case label missing")
    if not packet.get("claims", {}).get("economics_allowed", False):
        for term in ("赔率", "返点"):
            if term in content:
                errors.append(f"provider economics not verified; factual {term} statement is blocked")
    if article.get("rule_refs") != packet.get("immutable_facts", {}).get("rule_refs"):
        errors.append("article rule_refs differ from immutable draft packet")
    return DraftReview(passed=not errors, errors=errors, warnings=warnings)
