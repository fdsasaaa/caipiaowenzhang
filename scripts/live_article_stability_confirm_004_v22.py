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
from engine.stability_suite_v22 import stability_suite

OUTPUT = ROOT / "runtime" / "v22-stability-confirm-004"
TARGET_ID = "LCM-STAB-V22-004"
EXPECTED = [1000, 216, 96]


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def preflight_target() -> tuple[dict, dict]:
    matches = [(blueprint, expected) for blueprint, expected in stability_suite() if blueprint.get("article_id") == TARGET_ID]
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one {TARGET_ID}; got {len(matches)}")
    blueprint, expected = matches[0]
    if expected != EXPECTED:
        raise RuntimeError(f"frozen expected pipeline changed: expected={EXPECTED} got={expected}")
    packet = build_multistage_draft_packet(blueprint)
    result = packet["practicality"]["filter_pipeline_result"]
    actual = [result["starting_space"]] + [stage["after_space"] for stage in result["stages"]]
    if actual != EXPECTED:
        raise RuntimeError(f"live pipeline drift; refusing paid request: {actual}")
    if blueprint.get("play") != "后三直选":
        raise RuntimeError("case 004 play changed")
    if blueprint.get("technique_atoms") != ["compound_selection", "odd_even_filter"]:
        raise RuntimeError("case 004 technique atoms changed")
    return blueprint, packet


def main() -> int:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print(json.dumps({"ok": False, "stage": "configuration", "error": "OPENAI_API_KEY missing"}, ensure_ascii=False))
        return 2
    try:
        blueprint, packet = preflight_target()
    except RuntimeError as exc:
        print(json.dumps({"ok": False, "stage": "preflight", "error": str(exc)}, ensure_ascii=False))
        return 3

    base_url = normalize_base_url(os.getenv("OPENAI_BASE_URL"))
    model = os.getenv("OPENAI_MODEL") or "gpt-5.4-mini"
    transport = make_responses_transport(base_url)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    try:
        generated = generate_multistage_article(packet, model=model, api_key=api_key, transport=transport, timeout=240)
    except GenerationError as exc:
        summary = {
            "ok": False,
            "stage": "v22-stability-confirm-004",
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
        print("LIVE_STABILITY_004_JSON_START")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        print("LIVE_STABILITY_004_JSON_END")
        return 6

    approval = evaluate_for_approval(packet, generated.article)
    multistage = evaluate_multistage(packet, generated.article)
    approved = approval.approved and multistage.passed
    result = {
        "article_id": blueprint["article_id"],
        "play": blueprint["play"],
        "technique_atoms": blueprint["technique_atoms"],
        "title": generated.article.get("title"),
        "primary_keyword": generated.article.get("primary_keyword"),
        "generated": True,
        "approved": approved,
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
        "stage": "v22-stability-confirm-004",
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
        "approval_errors": result["approval_errors"],
        "multistage_errors": result["multistage_errors"],
        "response_id": result["response_id"],
        "pipeline": EXPECTED,
        "registry_write": False,
        "website_write": False,
        "scheduled": False,
        "published": False,
    }
    _write_json(OUTPUT / "summary.json", summary)
    print("LIVE_STABILITY_004_JSON_START")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("LIVE_STABILITY_004_JSON_END")
    return 0 if approved else 7


if __name__ == "__main__":
    raise SystemExit(main())
