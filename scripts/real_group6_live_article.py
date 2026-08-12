from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.ai_generation import GenerationError
from engine.approval import evaluate_for_approval
from engine.provider_transport import make_responses_transport, normalize_base_url
from engine.real_group6_ai_generation import generate_real_group6_article
from engine.real_group6_article_contract import (
    ARTICLE_ID,
    DOMAIN_BOUNDARY,
    FAMILY_ID,
    PRIMARY_KEYWORD,
    SOURCE_BOUNDARY,
    SOURCE_REF,
    build_real_group6_article_packet,
    evaluate_real_group6_article,
)

OUTPUT = ROOT / "runtime" / "real-group6-live-v2"
EXPECTED = {
    "article_id": ARTICLE_ID,
    "primary_keyword": PRIMARY_KEYWORD,
    "family_id": FAMILY_ID,
    "source_refs": [SOURCE_REF],
    "rule_refs": ["SSC-HIST-MECH-3STAR-GROUP6-V1"],
    "group_mode": "group6",
    "mode_owner": "system_research",
    "candidate_unit_count": 120,
    "ordered_structure_size": 720,
    "global_structure_share": 0.72,
    "target_play_full_domain_coverage": 1.0,
    "target_coverage_ceiling": 0.90,
    "full_domain_executable": False,
    "normalized_bets_allowed": False,
    "policy_ref": "USER-BET-COMPLIANCE-90-V1",
}


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def assert_exact_group6_case(packet: dict) -> dict:
    contract = packet.get("real_group6_validation") or {}
    binding = contract.get("binding") or {}
    actual = {
        "article_id": packet.get("article_id"),
        "primary_keyword": packet.get("seo", {}).get("primary_keyword"),
        "family_id": packet.get("immutable_facts", {}).get("technique_family"),
        "source_refs": packet.get("immutable_facts", {}).get("source_refs"),
        "rule_refs": packet.get("immutable_facts", {}).get("rule_refs"),
        "group_mode": binding.get("group_mode"),
        "mode_owner": (binding.get("mode_provenance") or {}).get("owner"),
        "candidate_unit_count": contract.get("group6_unit_count"),
        "ordered_structure_size": contract.get("ordered_group6_outcome_count"),
        "global_structure_share": contract.get("global_structure_share"),
        "target_play_full_domain_coverage": contract.get("target_play_full_domain_coverage"),
        "target_coverage_ceiling": contract.get("target_coverage_ceiling"),
        "full_domain_executable": contract.get("full_domain_executable_portfolio_allowed"),
        "normalized_bets_allowed": contract.get("normalized_bets_allowed"),
        "policy_ref": (packet.get("compliance") or {}).get("policy_ref"),
    }
    if actual != EXPECTED:
        raise RuntimeError(
            "real-family group6 target changed; refusing provider request: "
            + json.dumps(actual, ensure_ascii=False, sort_keys=True)
        )
    if binding.get("source_did_not_choose_mode") is not True:
        raise RuntimeError("group6 source/system mode ownership boundary changed")
    if SOURCE_BOUNDARY not in build_real_group6_article_packet()["real_group6_validation"]["source_boundary"]:
        raise RuntimeError("group6 source boundary changed")
    if DOMAIN_BOUNDARY not in build_real_group6_article_packet()["real_group6_validation"]["domain_boundary"]:
        raise RuntimeError("group6 coverage boundary changed")
    return actual


def build_preflight_summary() -> dict:
    packet = build_real_group6_article_packet()
    actual = assert_exact_group6_case(packet)
    return {
        "ok": True,
        "stage": "real-group6-live-v2-preflight",
        **actual,
        "provider_call": False,
        "registry_write": False,
        "website_write": False,
        "scheduled": False,
        "published": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Single real-family group6 article acceptance")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    packet = build_real_group6_article_packet()
    try:
        actual = assert_exact_group6_case(packet)
    except RuntimeError as exc:
        print(json.dumps({"ok": False, "stage": "preflight", "error": str(exc)}, ensure_ascii=False))
        return 3

    if args.preflight_only:
        summary = build_preflight_summary()
        _write_json(args.output / "preflight-summary.json", summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print(json.dumps({"ok": False, "stage": "configuration", "error": "OPENAI_API_KEY missing"}, ensure_ascii=False))
        return 2

    base_url = normalize_base_url(os.getenv("OPENAI_BASE_URL"))
    model = os.getenv("OPENAI_MODEL") or "gpt-5.4-mini"
    transport = make_responses_transport(base_url)
    args.output.mkdir(parents=True, exist_ok=True)

    try:
        generated = generate_real_group6_article(
            packet,
            model=model,
            api_key=api_key,
            transport=transport,
            timeout=300,
        )
    except GenerationError as exc:
        summary = {
            "ok": False,
            "stage": "real-group6-live-v2",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "base_url": base_url,
            "model": model,
            "requested": 1,
            "generated": 0,
            "approved": 0,
            "error": str(exc),
            "registry_write": False,
            "website_write": False,
            "scheduled": False,
            "published": False,
        }
        _write_json(args.output / "summary.json", summary)
        print("REAL_GROUP6_LIVE_V2_JSON_START")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        print("REAL_GROUP6_LIVE_V2_JSON_END")
        return 6

    approval = evaluate_for_approval(packet, generated.article)
    group6_quality = evaluate_real_group6_article(generated.article)
    approved = approval.approved and group6_quality.passed

    result = {
        "article_id": packet.get("article_id"),
        "title": generated.article.get("title"),
        "primary_keyword": generated.article.get("primary_keyword"),
        "generated": True,
        "approved": approved,
        "approval_status": approval.status,
        "quality_score": approval.quality_score,
        "editorial_score": approval.editorial_score,
        "group6_quality_score": group6_quality.score,
        "approval_errors": approval.errors,
        "approval_warnings": approval.warnings,
        "group6_quality_errors": group6_quality.errors,
        "response_id": generated.response_id,
        "article": generated.article,
        "approved_package_preview": approval.publish_package if approved else None,
        "registry_record_preview": approval.registry_record,
        "locked_contract": actual,
        "registry_write": False,
        "website_write": False,
        "scheduled": False,
        "published": False,
    }
    _write_json(args.output / "result.json", result)

    summary = {
        "ok": approved,
        "stage": "real-group6-live-v2",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "model": model,
        "requested": 1,
        "generated": 1,
        "approved": 1 if approved else 0,
        "failed": 0 if approved else 1,
        "article_id": result["article_id"],
        "title": result["title"],
        "primary_keyword": result["primary_keyword"],
        "quality_score": result["quality_score"],
        "editorial_score": result["editorial_score"],
        "group6_quality_score": result["group6_quality_score"],
        "response_id": result["response_id"],
        "approval_errors": result["approval_errors"],
        "group6_quality_errors": result["group6_quality_errors"],
        "locked_contract": actual,
        "registry_write": False,
        "website_write": False,
        "scheduled": False,
        "published": False,
    }
    _write_json(args.output / "summary.json", summary)
    print("REAL_GROUP6_LIVE_V2_JSON_START")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("REAL_GROUP6_LIVE_V2_JSON_END")
    return 0 if approved else 7


if __name__ == "__main__":
    raise SystemExit(main())
