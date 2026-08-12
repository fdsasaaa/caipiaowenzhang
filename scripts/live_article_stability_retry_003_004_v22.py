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

OUTPUT = ROOT / "runtime" / "v22-stability-retry-003-004"
TARGET_IDS = {"LCM-STAB-V22-003", "LCM-STAB-V22-004"}
EXPECTED = {
    "LCM-STAB-V22-003": [1000, 375, 300],
    "LCM-STAB-V22-004": [1000, 216, 96],
}


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def preflight_targets() -> list[tuple[dict, dict]]:
    selected = []
    for blueprint, expected in stability_suite():
        article_id = blueprint.get("article_id")
        if article_id not in TARGET_IDS:
            continue
        if expected != EXPECTED[article_id]:
            raise RuntimeError(
                f"{article_id} frozen expected pipeline changed: expected={EXPECTED[article_id]} got={expected}"
            )
        packet = build_multistage_draft_packet(blueprint)
        result = packet["practicality"]["filter_pipeline_result"]
        actual = [result["starting_space"]] + [stage["after_space"] for stage in result["stages"]]
        if actual != EXPECTED[article_id]:
            raise RuntimeError(
                f"{article_id} live pipeline drift; refusing targeted paid request: {actual}"
            )
        selected.append((blueprint, packet))
    ids = {blueprint["article_id"] for blueprint, _ in selected}
    if ids != TARGET_IDS or len(selected) != 2:
        raise RuntimeError(f"targeted retry must contain exactly 003 and 004; got={sorted(ids)}")
    return selected


def main() -> int:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print(json.dumps({"ok": False, "stage": "configuration", "error": "OPENAI_API_KEY missing"}, ensure_ascii=False))
        return 2
    try:
        prepared = preflight_targets()
    except RuntimeError as exc:
        print(json.dumps({"ok": False, "stage": "preflight", "error": str(exc)}, ensure_ascii=False))
        return 3

    base_url = normalize_base_url(os.getenv("OPENAI_BASE_URL"))
    model = os.getenv("OPENAI_MODEL") or "gpt-5.4-mini"
    transport = make_responses_transport(base_url)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    cases = []
    for blueprint, packet in prepared:
        article_id = blueprint["article_id"]
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
                "article_id": article_id,
                "title": blueprint.get("title"),
                "play": blueprint.get("play"),
                "generated": False,
                "approved": False,
                "error": str(exc),
            }
            cases.append(item)
            _write_json(OUTPUT / f"{article_id}-result.json", item)
            continue

        approval = evaluate_for_approval(packet, generated.article)
        multistage = evaluate_multistage(packet, generated.article)
        approved = approval.approved and multistage.passed
        item = {
            "article_id": article_id,
            "title": generated.article.get("title"),
            "play": blueprint.get("play"),
            "technique_atoms": blueprint.get("technique_atoms"),
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
        cases.append(item)
        _write_json(OUTPUT / f"{article_id}-result.json", item)

    generated_count = sum(bool(item.get("generated")) for item in cases)
    approved_count = sum(bool(item.get("approved")) for item in cases)
    summary = {
        "ok": approved_count == 2,
        "stage": "v22-stability-targeted-retry-003-004",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "model": model,
        "requested": 2,
        "generated": generated_count,
        "approved": approved_count,
        "failed": 2 - approved_count,
        "registry_write": False,
        "website_write": False,
        "scheduled": False,
        "published": False,
        "cases": [
            {
                key: item.get(key)
                for key in (
                    "article_id", "play", "title", "generated", "approved", "quality_score",
                    "editorial_score", "multistage_score", "response_id", "approval_errors",
                    "multistage_errors", "error",
                )
            }
            for item in cases
        ],
    }
    _write_json(OUTPUT / "summary.json", summary)
    print("LIVE_STABILITY_RETRY_V22_JSON_START")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("LIVE_STABILITY_RETRY_V22_JSON_END")
    return 0 if summary["ok"] else 7


if __name__ == "__main__":
    raise SystemExit(main())
