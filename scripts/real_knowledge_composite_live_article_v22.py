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
from engine.batch_quality_v22 import evaluate_multistage
from engine.provider_transport import make_responses_transport, normalize_base_url
from engine.real_knowledge_composite_ai_generation import generate_composite_real_knowledge_article
from engine.real_knowledge_composite_article_contract import (
    ARTICLE_ID,
    CANDIDATE_INTEGRITY_BOUNDARY,
    ORDER_BOUNDARY,
    SOURCE_BOUNDARY,
    build_composite_article_packet,
    evaluate_composite_article_content,
)
from engine.real_knowledge_composition import EXPECTED_CANDIDATE_SHA256


OUTPUT = ROOT / "runtime" / "real-knowledge-composite-live-v22"
EXPECTED = {
    "article_id": ARTICLE_ID,
    "primary_keyword": "分分彩后三和值跨度技巧",
    "rule_refs": ["SSC-HIST-MECH-3STAR-LAST-V1"],
    "source_refs": ["BRBCW-006020", "BRBCW-002590"],
    "starting_space": 1000,
    "stage_after_spaces": [760, 534],
    "stage_excluded_spaces": [240, 226],
    "final_space": 534,
    "total_excluded": 466,
    "final_candidate_sha256": EXPECTED_CANDIDATE_SHA256,
}


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def assert_exact_composite_case(packet: dict) -> dict:
    result = packet.get("practicality", {}).get("filter_pipeline_result") or {}
    contract = packet.get("real_knowledge_composition") or {}
    actual = {
        "article_id": packet.get("article_id"),
        "primary_keyword": packet.get("seo", {}).get("primary_keyword"),
        "rule_refs": packet.get("immutable_facts", {}).get("rule_refs"),
        "source_refs": packet.get("immutable_facts", {}).get("source_refs"),
        "starting_space": result.get("starting_space"),
        "stage_after_spaces": [stage.get("after_space") for stage in (result.get("stages") or [])],
        "stage_excluded_spaces": [stage.get("excluded_space") for stage in (result.get("stages") or [])],
        "final_space": result.get("final_space"),
        "total_excluded": result.get("total_excluded"),
        "final_candidate_sha256": contract.get("final_candidate_sha256"),
    }
    if actual != EXPECTED:
        raise RuntimeError(
            "composite real-knowledge target changed; refusing provider request: "
            + json.dumps(actual, ensure_ascii=False, sort_keys=True)
        )
    if contract.get("must_list_all_final_candidates") is not False:
        raise RuntimeError("composite contract unexpectedly requires full 534-candidate dump")
    for sentence in (SOURCE_BOUNDARY, ORDER_BOUNDARY, CANDIDATE_INTEGRITY_BOUNDARY):
        if sentence not in contract.values():
            raise RuntimeError("required composite boundary sentence changed")
    return actual


def build_preflight_summary() -> dict:
    packet = build_composite_article_packet()
    actual = assert_exact_composite_case(packet)
    return {
        "ok": True,
        "stage": "real-knowledge-composite-live-v22-preflight",
        **actual,
        "spot_checks": packet["real_knowledge_composition"]["spot_checks"],
        "paid_model_call": False,
        "registry_write": False,
        "website_write": False,
        "scheduled": False,
        "published": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Single cross-family real-knowledge V2.2 article acceptance")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    packet = build_composite_article_packet()
    try:
        actual = assert_exact_composite_case(packet)
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
        generated = generate_composite_real_knowledge_article(
            packet,
            model=model,
            api_key=api_key,
            transport=transport,
            timeout=300,
        )
    except GenerationError as exc:
        summary = {
            "ok": False,
            "stage": "real-knowledge-composite-live-v22",
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
        print("REAL_KNOWLEDGE_COMPOSITE_LIVE_V22_JSON_START")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        print("REAL_KNOWLEDGE_COMPOSITE_LIVE_V22_JSON_END")
        return 6

    approval = evaluate_for_approval(packet, generated.article)
    multistage = evaluate_multistage(packet, generated.article)
    composite_quality = evaluate_composite_article_content(generated.article)
    approved = approval.approved and multistage.passed and composite_quality.passed

    result = {
        "article_id": packet.get("article_id"),
        "title": generated.article.get("title"),
        "primary_keyword": generated.article.get("primary_keyword"),
        "generated": True,
        "approved": approved,
        "approval_status": approval.status,
        "quality_score": approval.quality_score,
        "editorial_score": approval.editorial_score,
        "multistage_score": multistage.score,
        "composite_quality_score": composite_quality.score,
        "approval_errors": approval.errors,
        "approval_warnings": approval.warnings,
        "multistage_errors": multistage.errors,
        "multistage_warnings": multistage.warnings,
        "composite_quality_errors": composite_quality.errors,
        "composite_quality_warnings": composite_quality.warnings,
        "response_id": generated.response_id,
        "pipeline_result": packet["practicality"]["filter_pipeline_result"],
        "spot_checks": packet["real_knowledge_composition"]["spot_checks"],
        "article": generated.article,
        "approved_package_preview": approval.publish_package if approved else None,
        "registry_record_preview": approval.registry_record,
        "registry_write": False,
        "website_write": False,
        "scheduled": False,
        "published": False,
    }
    _write_json(args.output / "result.json", result)

    summary = {
        "ok": approved,
        "stage": "real-knowledge-composite-live-v22",
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
        "multistage_score": result["multistage_score"],
        "composite_quality_score": result["composite_quality_score"],
        "response_id": result["response_id"],
        "approval_errors": result["approval_errors"],
        "multistage_errors": result["multistage_errors"],
        "composite_quality_errors": result["composite_quality_errors"],
        "locked_contract": EXPECTED,
        "registry_write": False,
        "website_write": False,
        "scheduled": False,
        "published": False,
    }
    _write_json(args.output / "summary.json", summary)
    print("REAL_KNOWLEDGE_COMPOSITE_LIVE_V22_JSON_START")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("REAL_KNOWLEDGE_COMPOSITE_LIVE_V22_JSON_END")
    return 0 if approved else 7


if __name__ == "__main__":
    raise SystemExit(main())
