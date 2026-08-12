from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.ai_generation import GenerationError
from engine.ai_generation_v22 import generate_multistage_article
from engine.approval import evaluate_for_approval
from engine.batch_quality_v22 import evaluate_multistage
from engine.draft_pipeline_v22 import build_multistage_draft_packet
from engine.provider_transport import make_responses_transport, normalize_base_url

BLUEPRINT = ROOT / "agent" / "benchmarks" / "v22-live-batch" / "004-blueprint.json"
OUTPUT = ROOT / "runtime" / "v22-live-confirm-004"
EXPECTED_ARTICLE_ID = "LCM-SMOKE-V22-004"
EXPECTED_PIPELINE = {
    "starting_space": 45,
    "stage_after_spaces": [10, 7],
    "stage_excluded_spaces": [35, 3],
    "final_space": 7,
    "total_excluded": 38,
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def _assert_exact_case(packet: dict, blueprint: dict) -> None:
    if blueprint.get("article_id") != EXPECTED_ARTICLE_ID:
        raise RuntimeError("targeted runner refuses any article except LCM-SMOKE-V22-004")
    result = packet.get("practicality", {}).get("filter_pipeline_result") or {}
    stages = result.get("stages") or []
    actual = {
        "starting_space": result.get("starting_space"),
        "stage_after_spaces": [stage.get("after_space") for stage in stages],
        "stage_excluded_spaces": [stage.get("excluded_space") for stage in stages],
        "final_space": result.get("final_space"),
        "total_excluded": result.get("total_excluded"),
    }
    if actual != EXPECTED_PIPELINE:
        raise RuntimeError(
            "case 004 pipeline changed; refusing paid request: "
            + json.dumps(actual, ensure_ascii=False, sort_keys=True)
        )


def main() -> int:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print(json.dumps({"ok": False, "stage": "configuration", "error": "OPENAI_API_KEY missing"}, ensure_ascii=False))
        return 2

    blueprint = _load(BLUEPRINT)
    packet = build_multistage_draft_packet(blueprint)
    try:
        _assert_exact_case(packet, blueprint)
    except RuntimeError as exc:
        print(json.dumps({"ok": False, "stage": "preflight", "error": str(exc)}, ensure_ascii=False))
        return 3

    base_url = normalize_base_url(os.getenv("OPENAI_BASE_URL"))
    model = os.getenv("OPENAI_MODEL") or "gpt-5.4-mini"
    transport = make_responses_transport(base_url)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    try:
        generated = generate_multistage_article(
            packet,
            model=model,
            api_key=api_key,
            transport=transport,
            timeout=240,
        )
    except GenerationError as exc:
        summary = {
            "ok": False,
            "stage": "v22-004-live-confirm",
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
        _write_json(OUTPUT / "summary.json", summary)
        print("LIVE_004_V22_JSON_START")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        print("LIVE_004_V22_JSON_END")
        return 6

    approval = evaluate_for_approval(packet, generated.article)
    multistage = evaluate_multistage(packet, generated.article)
    approved = approval.approved and multistage.passed

    result = {
        "article_id": blueprint.get("article_id"),
        "title": generated.article.get("title"),
        "primary_keyword": generated.article.get("primary_keyword"),
        "generated": True,
        "approved": approved,
        "approval_status": approval.status,
        "quality_score": approval.quality_score,
        "editorial_score": approval.editorial_score,
        "multistage_score": multistage.score,
        "approval_errors": approval.errors,
        "approval_warnings": approval.warnings,
        "multistage_errors": multistage.errors,
        "multistage_warnings": multistage.warnings,
        "response_id": generated.response_id,
        "pipeline_result": packet["practicality"]["filter_pipeline_result"],
        "article": generated.article,
        "approved_package": approval.publish_package if approved else None,
    }
    _write_json(OUTPUT / "004-result.json", result)

    summary = {
        "ok": approved,
        "stage": "v22-004-live-confirm",
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
        "response_id": result["response_id"],
        "approval_errors": result["approval_errors"],
        "multistage_errors": result["multistage_errors"],
        "pipeline": EXPECTED_PIPELINE,
        "registry_write": False,
        "website_write": False,
        "scheduled": False,
        "published": False,
    }
    _write_json(OUTPUT / "summary.json", summary)
    print("LIVE_004_V22_JSON_START")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("LIVE_004_V22_JSON_END")
    return 0 if approved else 7


if __name__ == "__main__":
    raise SystemExit(main())
