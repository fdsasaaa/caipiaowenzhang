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
from engine.stability_suite_20_v22 import stability_suite_20

OUTPUT = ROOT / "runtime" / "v22-stability-20"
EXPECTED_COUNT = 20


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def preflight_suite() -> list[tuple[dict, dict]]:
    suite = stability_suite_20()
    if len(suite) != EXPECTED_COUNT:
        raise RuntimeError(f"stability-20 suite must contain exactly {EXPECTED_COUNT} cases")

    article_ids: set[str] = set()
    keywords: set[str] = set()
    prepared: list[tuple[dict, dict]] = []

    for blueprint, expected in suite:
        article_id = str(blueprint.get("article_id") or "")
        keyword = str(blueprint.get("primary_keyword") or "")
        if not article_id or article_id in article_ids:
            raise RuntimeError(f"duplicate or missing article_id: {article_id!r}")
        if not keyword or keyword in keywords:
            raise RuntimeError(f"duplicate or missing primary_keyword: {keyword!r}")
        article_ids.add(article_id)
        keywords.add(keyword)

        packet = build_multistage_draft_packet(blueprint)
        result = packet.get("practicality", {}).get("filter_pipeline_result") or {}
        stages = result.get("stages") or []
        actual = [result.get("starting_space")] + [stage.get("after_space") for stage in stages]
        if actual != expected:
            raise RuntimeError(
                f"{article_id} pipeline changed; refusing paid batch: expected={expected} actual={actual}"
            )
        if result.get("final_space") != expected[-1]:
            raise RuntimeError(f"{article_id} final_space mismatch")
        if len(stages) not in {2, 3}:
            raise RuntimeError(f"{article_id} must use two or three frozen stages")
        if any(stage.get("after_space", 0) >= stage.get("before_space", 0) for stage in stages):
            raise RuntimeError(f"{article_id} contains non-reducing stage")
        prepared.append((blueprint, packet))

    return prepared


def main() -> int:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print(json.dumps({"ok": False, "stage": "configuration", "error": "OPENAI_API_KEY missing"}, ensure_ascii=False))
        return 2

    try:
        prepared = preflight_suite()
    except RuntimeError as exc:
        print(json.dumps({"ok": False, "stage": "preflight", "error": str(exc)}, ensure_ascii=False))
        return 3

    base_url = normalize_base_url(os.getenv("OPENAI_BASE_URL"))
    model = os.getenv("OPENAI_MODEL") or "gpt-5.4-mini"
    transport = make_responses_transport(base_url)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    cases: list[dict] = []
    for index, (blueprint, packet) in enumerate(prepared, start=1):
        case_id = str(blueprint["article_id"]).rsplit("-", 1)[-1]
        try:
            generated = generate_multistage_article(
                packet,
                model=model,
                api_key=api_key,
                transport=transport,
                timeout=240,
            )
        except GenerationError as exc:
            item = {
                "case_id": case_id,
                "article_id": blueprint.get("article_id"),
                "play": blueprint.get("play"),
                "technique_atoms": blueprint.get("technique_atoms"),
                "title": blueprint.get("title"),
                "primary_keyword": blueprint.get("primary_keyword"),
                "generated": False,
                "approved": False,
                "failure_class": "transport_or_generation",
                "error": str(exc),
            }
            cases.append(item)
            _write_json(OUTPUT / f"{case_id}-result.json", item)
            continue

        approval = evaluate_for_approval(packet, generated.article)
        multistage = evaluate_multistage(packet, generated.article)
        approved = approval.approved and multistage.passed
        item = {
            "case_id": case_id,
            "article_id": blueprint.get("article_id"),
            "play": blueprint.get("play"),
            "technique_atoms": blueprint.get("technique_atoms"),
            "title": generated.article.get("title"),
            "primary_keyword": generated.article.get("primary_keyword"),
            "generated": True,
            "approved": approved,
            "failure_class": None if approved else "content_approval",
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
        cases.append(item)
        _write_json(OUTPUT / f"{case_id}-result.json", item)

    generated_count = sum(1 for item in cases if item.get("generated"))
    transport_failed = EXPECTED_COUNT - generated_count
    approved_count = sum(1 for item in cases if item.get("approved"))
    content_failed = generated_count - approved_count
    summary = {
        "ok": approved_count == EXPECTED_COUNT,
        "stage": "v22-stability-20-live",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "model": model,
        "requested": EXPECTED_COUNT,
        "generated": generated_count,
        "transport_failed": transport_failed,
        "transport_success_rate": generated_count / EXPECTED_COUNT,
        "approved": approved_count,
        "content_failed": content_failed,
        "content_approval_rate": approved_count / generated_count if generated_count else 0.0,
        "overall_approval_rate": approved_count / EXPECTED_COUNT,
        "registry_write": False,
        "website_write": False,
        "scheduled": False,
        "published": False,
        "cases": [
            {
                key: item.get(key)
                for key in (
                    "case_id", "article_id", "play", "technique_atoms", "title", "primary_keyword",
                    "generated", "approved", "failure_class", "quality_score", "editorial_score",
                    "multistage_score", "response_id", "approval_errors", "multistage_errors", "error",
                )
            }
            for item in cases
        ],
    }
    _write_json(OUTPUT / "summary.json", summary)
    print("LIVE_STABILITY_20_V22_JSON_START")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("LIVE_STABILITY_20_V22_JSON_END")
    return 0 if summary["ok"] else 7


if __name__ == "__main__":
    raise SystemExit(main())
