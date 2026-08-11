from __future__ import annotations

import os
from collections import Counter
from pathlib import Path

from .rules import load_rules, rule_capability
from .seo_priority import read_demand_signals
from .store import iter_registry

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_V2_ASSETS = (
    "engine/source_intelligence.py",
    "engine/knowledge_families_v2.py",
    "engine/ai_generation.py",
    "engine/claim_evidence.py",
    "engine/semantic_dedup.py",
    "engine/seo_priority.py",
    "engine/batch_production_v2.py",
    "scripts/ingest_sources_v2.py",
    "scripts/normalize_search_console_csv.py",
    "scripts/rank_topics_v2.py",
    "scripts/generate_and_review_v2.py",
    "scripts/produce_ranked_batch_v2.py",
)


def readiness_report(
    *,
    signals_path: Path | None = None,
    provider_id: str | None = None,
    lottery: str | None = None,
    play: str | None = None,
) -> dict:
    assets = {path: (ROOT / path).exists() for path in REQUIRED_V2_ASSETS}
    code_ready = all(assets.values())

    rules = load_rules()
    verified_mechanics = sum(
        1 for row in rules
        if row.get("status") == "verified" and row.get("scope", "full") in {"mechanics", "full"}
    )
    verified_economics = sum(
        1 for row in rules
        if row.get("status") == "verified" and row.get("scope", "full") in {"economics", "full"}
    )

    statuses = Counter(str(row.get("status") or "unknown") for row in iter_registry("articles"))
    dynamic_dir = ROOT / "knowledge" / "dynamic_families"
    dynamic_files = sorted(dynamic_dir.glob("*.jsonl")) if dynamic_dir.exists() else []
    dynamic_family_count = 0
    for path in dynamic_files:
        dynamic_family_count += sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())

    external_signals = []
    if signals_path is not None:
        external_signals = read_demand_signals(signals_path)

    api_configured = bool(os.getenv("OPENAI_API_KEY"))
    target = None
    if provider_id and lottery and play:
        target = rule_capability(provider_id, lottery, play)

    blockers = []
    if not code_ready:
        blockers.append("v2_code_assets_missing")
    if not api_configured:
        blockers.append("live_model_api_key_not_configured")
    if signals_path is None or not external_signals:
        blockers.append("seo_priority_has_no_external_demand_signals")
    if target is not None and not target.get("mechanics_verified"):
        blockers.append("target_mechanics_not_verified")
    if target is not None and not target.get("economics_verified"):
        blockers.append("target_economics_not_verified_for_money_payout_claims")

    return {
        "v2_code_ready": code_ready,
        "required_assets": assets,
        "live_model_generation_ready": code_ready and api_configured,
        "openai_api_key_configured": api_configured,
        "seo_signal_mode": "external_augmented" if external_signals else "internal_only",
        "external_signal_records": len(external_signals),
        "verified_mechanics_rules": verified_mechanics,
        "verified_economics_rules": verified_economics,
        "dynamic_family_files": len(dynamic_files),
        "dynamic_family_count": dynamic_family_count,
        "article_statuses": dict(sorted(statuses.items())),
        "target_capability": target,
        "target_live_generation_ready": bool(
            code_ready and api_configured and (target is None or target.get("mechanics_verified"))
        ),
        "blockers_or_external_dependencies": blockers,
        "publication_boundary": "article creation only; website scheduling/publishing remains separately gated",
    }
