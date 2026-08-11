from __future__ import annotations

import json
import math
from pathlib import Path

from .blueprints import generate_blueprints
from .seo_keywords import normalize_keyword


def read_demand_signals(path: Path | None) -> list[dict]:
    if path is None:
        return []
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("signals", payload.get("rows", payload)) if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            raise ValueError("demand signal JSON must be a list or signals/rows list")
        return [dict(x) for x in rows]
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _signal_key(row: dict) -> str:
    return normalize_keyword(row.get("primary_keyword") or row.get("query") or row.get("keyword"))


def _signal_index(rows: list[dict]) -> dict[str, dict]:
    grouped: dict[str, dict] = {}
    for row in rows:
        key = _signal_key(row)
        if not key:
            continue
        target = grouped.setdefault(key, {
            "primary_keyword": row.get("primary_keyword") or row.get("query") or row.get("keyword"),
            "impressions": 0.0,
            "clicks": 0.0,
            "weighted_position_num": 0.0,
            "weighted_position_den": 0.0,
            "search_volume": None,
            "competition": None,
            "source": row.get("source") or "external",
        })
        impressions = max(0.0, float(row.get("impressions") or 0))
        clicks = max(0.0, float(row.get("clicks") or 0))
        position = row.get("position")
        target["impressions"] += impressions
        target["clicks"] += clicks
        if position not in (None, ""):
            weight = max(impressions, 1.0)
            target["weighted_position_num"] += float(position) * weight
            target["weighted_position_den"] += weight
        if row.get("search_volume") not in (None, ""):
            target["search_volume"] = max(float(row["search_volume"]), float(target["search_volume"] or 0))
        if row.get("competition") not in (None, ""):
            target["competition"] = float(row["competition"])
    for target in grouped.values():
        impressions = target["impressions"]
        target["ctr"] = target["clicks"] / impressions if impressions > 0 else None
        den = target.pop("weighted_position_den")
        num = target.pop("weighted_position_num")
        target["position"] = num / den if den else None
    return grouped


def _support_score(count: int) -> float:
    return min(15.0, math.log1p(max(0, count)) / math.log(101) * 15.0)


def _external_score(signal: dict | None) -> tuple[float, list[str]]:
    if not signal:
        return 0.0, []
    score = 0.0
    reasons: list[str] = []
    impressions = float(signal.get("impressions") or 0)
    if impressions > 0:
        part = min(15.0, math.log1p(impressions) / math.log(10001) * 15.0)
        score += part
        reasons.append(f"external_impressions={int(impressions)}")
    position = signal.get("position")
    if position is not None:
        p = float(position)
        if 4 <= p <= 20:
            score += 10; reasons.append(f"ranking_opportunity_position={p:.1f}")
        elif 20 < p <= 50:
            score += 7; reasons.append(f"mid_tail_position={p:.1f}")
        elif 1 <= p < 4:
            score += 3; reasons.append(f"already_top_position={p:.1f}")
        elif p > 50:
            score += 4; reasons.append(f"low_visibility_position={p:.1f}")
    ctr = signal.get("ctr")
    if impressions >= 100 and ctr is not None and float(ctr) < 0.03:
        score += 5; reasons.append(f"ctr_gap={float(ctr):.3f}")
    volume = signal.get("search_volume")
    if volume is not None and float(volume) > 0:
        score += min(5.0, math.log1p(float(volume)) / math.log(10001) * 5.0)
        reasons.append(f"external_search_volume={int(float(volume))}")
    return min(35.0, score), reasons


def score_blueprint(blueprint: dict, signal: dict | None = None) -> dict:
    reasons: list[str] = []
    if blueprint.get("status") != "ready_for_draft":
        return {
            "article_id": blueprint.get("article_id"),
            "blueprint_id": blueprint.get("blueprint_id"),
            "title": blueprint.get("title"),
            "primary_keyword": blueprint.get("primary_keyword"),
            "eligible": False,
            "priority_score": 0.0,
            "priority_band": "blocked",
            "signal_mode": "external_augmented" if signal else "internal_only",
            "reasons": ["blueprint_not_ready", *blueprint.get("blockers", [])],
            "blueprint": blueprint,
            "demand_signal": signal,
        }

    score = 25.0
    reasons.append("verified_and_case_ready")
    support = int(blueprint.get("source_support_count") or 0)
    support_part = _support_score(support)
    score += support_part
    reasons.append(f"source_support={support}")

    risk = min(1.0, max(0.0, float(blueprint.get("source_risk_rate") or 0)))
    risk_part = 10.0 * (1.0 - risk)
    score += risk_part
    reasons.append(f"source_risk_rate={risk:.3f}")

    if blueprint.get("information_gain_type"):
        score += 5.0; reasons.append("explicit_information_gain")
    if not blueprint.get("keyword_owner_hits"):
        score += 5.0; reasons.append("primary_keyword_unowned")
    if not blueprint.get("duplicate_hits") and not blueprint.get("structural_duplicate_hits"):
        score += 10.0; reasons.append("novelty_gates_clear")

    external, external_reasons = _external_score(signal)
    score += external
    reasons.extend(external_reasons)
    score = round(min(100.0, score), 2)
    if score >= 80:
        band = "very_high"
    elif score >= 65:
        band = "high"
    elif score >= 50:
        band = "medium"
    else:
        band = "low"
    return {
        "article_id": blueprint.get("article_id"),
        "blueprint_id": blueprint.get("blueprint_id"),
        "title": blueprint.get("title"),
        "primary_keyword": blueprint.get("primary_keyword"),
        "eligible": True,
        "priority_score": score,
        "priority_band": band,
        "signal_mode": "external_augmented" if signal else "internal_only",
        "reasons": reasons,
        "blueprint": blueprint,
        "demand_signal": signal,
    }


def rank_blueprints(blueprints: list[dict], signals: list[dict] | None = None) -> list[dict]:
    index = _signal_index(signals or [])
    scored = []
    for blueprint in blueprints:
        key = normalize_keyword(blueprint.get("primary_keyword"))
        scored.append(score_blueprint(blueprint, index.get(key)))
    return sorted(scored, key=lambda row: (row["eligible"], row["priority_score"]), reverse=True)


def rank_generated_topics(provider_id: str, lottery: str, play: str, count: int = 20, signals: list[dict] | None = None) -> dict:
    result = generate_blueprints(provider_id, lottery, play, max(count * 3, count))
    ranking = rank_blueprints(result.get("blueprints", []), signals)
    return {
        "provider_id": provider_id,
        "lottery": lottery,
        "play": play,
        "signal_mode": "external_augmented" if signals else "internal_only",
        "requested": count,
        "ranked": ranking[:count],
        "eligible": sum(1 for row in ranking if row["eligible"]),
        "blocked": sum(1 for row in ranking if not row["eligible"]),
    }
