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
from engine.real_knowledge_ai_generation import generate_real_knowledge_article
from engine.real_knowledge_live_validation import (
    TARGET_ARTICLE_ID,
    build_real_knowledge_live_packet,
    evaluate_real_knowledge_article,
)


OUTPUT = ROOT / "runtime" / "real-knowledge-live-v22"
EXPECTED = {
    "article_id": TARGET_ARTICLE_ID,
    "family": "FAM-32137acbb90340b9",
    "source_refs": ["BRBCW-003787"],
    "rule_refs": ["SSC-HIST-MECH-LAST2-BSOE-V1"],
    "starting_space": 100,
    "stage_after_spaces": [50, 26],
    "stage_excluded_spaces": [50, 24],
    "final_space": 26,
    "total_excluded": 74,
    "final_candidates": [
        "05", "07", "09", "16", "18", "25", "27", "29", "36", "38", "45", "47", "49",
        "50", "52", "54", "61", "63", "70", "72", "74", "81", "83", "90", "92", "94",
    ],
}


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def assert_exact_real_knowledge_case(packet: dict) -> dict:
    facts = packet.get("immutable_facts") or {}
    contract = packet.get("real_knowledge_validation") or {}
    result = packet.get("practicality", {}).get("filter_pipeline_result") or {}
    stages = result.get("stages") or []
    actual = {
        "article_id": packet.get("article_id"),
        "family": facts.get("technique_family"),
        "source_refs": facts.get("source_refs"),
        "rule_refs": facts.get("rule_refs"),
        "starting_space": result.get("starting_space"),
        "stage_after_spaces": [stage.get("after_space") for stage in stages],
        "stage_excluded_spaces": [stage.get("excluded_space") for stage in stages],
        "final_space": result.get("final_space"),
        "total_excluded": result.get("total_excluded"),
        "final_candidates": contract.get("final_candidates"),
    }
    if actual != EXPECTED:
        raise RuntimeError(
            "real-knowledge target changed; refusing provider request: "
            + json.dumps(actual, ensure_ascii=False, sort_keys=True)
        )
    for key in ("registry_write", "website_write", "scheduled", "published"):
        if contract.get(key) is not False:
            raise RuntimeError(f"real-knowledge validation write/publish boundary changed: {key}")
    return actual


def build_preflight_summary() -> dict:
    packet = build_real_knowledge_live_packet()
    actual = assert_exact_real_knowledge_case(packet)
    return {
        "ok": True,
        "stage": "real-knowledge-live-v22-preflight",
        "article_id": actual["article_id"],
        "family": actual["family"],
        "source_refs": actual["source_refs"],
        "rule_refs": actual["rule_refs"],
        "pipeline": {
            "starting_space": actual["starting_space"],
            "stage_after_spaces": actual["stage_after_spaces"],
            "stage_excluded_spaces": actual["stage_excluded_spaces"],
            "final_space": actual["final_space"],
            "total_excluded": actual["total_excluded"],
        },
        "final_candidates": actual["final_candidates"],
        "paid_model_call": False,
        "registry_write": False,
        "website_write": False,
        "scheduled": False,
        "published": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Single real-knowledge V2.2 article acceptance")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    packet = build_real_knowledge_live_packet()
    try:
        actual = assert_exact_real_knowledge_case(packet)
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
        generated = generate_real_knowledge_article(
            packet,
            model=model,
            api_key=api_key,
            transport=transport,
            timeout=300,
        )
    except GenerationError as exc:
        summary = {
            "ok": False,
            "stage": "real-knowledge-live-v22",
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
        print("REAL_KNOWLEDGE_LIVE_V22_JSON_START")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        print("REAL_KNOWLEDGE_LIVE_V22_JSON_END")
        return 6

    approval = evaluate_for_approval(packet, generated.article)
    multistage = evaluate_multistage(packet, generated.article)
    real_quality = evaluate_real_knowledge_article(packet, generated.article)
    approved = approval.approved and multistage.passed and real_quality.passed

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
        "real_knowledge_score": real_quality.score,
        "approval_errors": approval.errors,
        "approval_warnings": approval.warnings,
        "multistage_errors": multistage.errors,
        "multistage_warnings": multistage.warnings,
        "real_knowledge_errors": real_quality.errors,
        "real_knowledge_warnings": real_quality.warnings,
        "response_id": generated.response_id,
        "pipeline_result": packet["practicality"]["filter_pipeline_result"],
        "final_candidates": actual["final_candidates"],
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
        "stage": "real-knowledge-live-v22",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "model": model,
        "requested": 1,
        "generated": 1,
        "approved": 1 if approved else 0,
        "failed": 0 if approved else 1,
        "article_id": result["article_id"],
        "family": actual["family"],
        "source_refs": actual["source_refs"],
        "rule_refs": actual["rule_refs"],
        "title": result["title"],
        "primary_keyword": result["primary_keyword"],
        "quality_score": result["quality_score"],
        "editorial_score": result["editorial_score"],
        "multistage_score": result["multistage_score"],
        "real_knowledge_score": result["real_knowledge_score"],
        "response_id": result["response_id"],
        "approval_errors": result["approval_errors"],
        "multistage_errors": result["multistage_errors"],
        "real_knowledge_errors": result["real_knowledge_errors"],
        "pipeline": EXPECTED,
        "registry_write": False,
        "website_write": False,
        "scheduled": False,
        "published": False,
    }
    _write_json(args.output / "summary.json", summary)
    print("REAL_KNOWLEDGE_LIVE_V22_JSON_START")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("REAL_KNOWLEDGE_LIVE_V22_JSON_END")
    return 0 if approved else 7


if __name__ == "__main__":
    raise SystemExit(main())
