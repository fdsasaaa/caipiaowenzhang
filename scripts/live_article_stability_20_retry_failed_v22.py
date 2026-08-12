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

OUTPUT = ROOT / "runtime" / "v22-stability-20-retry"
TARGET_IDS = (
    "LCM-STAB20-V22-012",
    "LCM-STAB20-V22-013",
    "LCM-STAB20-V22-014",
    "LCM-STAB20-V22-018",
    "LCM-STAB20-V22-020",
    "LCM-STAB20-V22-029",
    "LCM-STAB20-V22-030",
)
EXPECTED = {
    "LCM-STAB20-V22-012": [1000, 690, 285],
    "LCM-STAB20-V22-013": [1000, 216, 120],
    "LCM-STAB20-V22-014": [1000, 375, 234, 141],
    "LCM-STAB20-V22-018": [1000, 516, 198],
    "LCM-STAB20-V22-020": [1000, 216, 81],
    "LCM-STAB20-V22-029": [45, 15, 9, 5],
    "LCM-STAB20-V22-030": [45, 25, 16, 8],
}


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def preflight_targets() -> list[tuple[dict, dict]]:
    suite = stability_suite_20()
    by_id = {blueprint["article_id"]: (blueprint, expected) for blueprint, expected in suite}
    if set(TARGET_IDS) != set(EXPECTED):
        raise RuntimeError("target/expected ID contract mismatch")

    selected: list[tuple[dict, dict]] = []
    for article_id in TARGET_IDS:
        if article_id not in by_id:
            raise RuntimeError(f"targeted retry case missing: {article_id}")
        blueprint, expected = by_id[article_id]
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
        if not blueprint.get("technique_atoms"):
            raise RuntimeError(f"{article_id} technique atoms missing")
        selected.append((blueprint, packet))

    if [blueprint["article_id"] for blueprint, _ in selected] != list(TARGET_IDS):
        raise RuntimeError("targeted retry order/identity changed")
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

    cases: list[dict] = []
    for blueprint, packet in prepared:
        article_id = blueprint["article_id"]
        case_id = article_id.rsplit("-", 1)[-1]
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
                "article_id": article_id,
                "play": blueprint.get("play"),
                "technique_atoms": blueprint.get("technique_atoms"),
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
            "article_id": article_id,
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
    approved_count = sum(1 for item in cases if item.get("approved"))
    summary = {
        "ok": approved_count == len(TARGET_IDS),
        "stage": "v22-stability-20-targeted-retry",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "model": model,
        "requested": len(TARGET_IDS),
        "generated": generated_count,
        "transport_failed": len(TARGET_IDS) - generated_count,
        "approved": approved_count,
        "content_failed": generated_count - approved_count,
        "transport_success_rate": generated_count / len(TARGET_IDS),
        "content_approval_rate": approved_count / generated_count if generated_count else 0.0,
        "registry_write": False,
        "website_write": False,
        "scheduled": False,
        "published": False,
        "cases": [
            {
                key: item.get(key)
                for key in (
                    "case_id", "article_id", "play", "generated", "approved", "failure_class",
                    "quality_score", "editorial_score", "multistage_score", "response_id",
                    "approval_errors", "multistage_errors", "error",
                )
            }
            for item in cases
        ],
    }
    _write_json(OUTPUT / "summary.json", summary)
    print("LIVE_STABILITY_20_RETRY_JSON_START")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("LIVE_STABILITY_20_RETRY_JSON_END")
    return 0 if summary["ok"] else 7


if __name__ == "__main__":
    raise SystemExit(main())
