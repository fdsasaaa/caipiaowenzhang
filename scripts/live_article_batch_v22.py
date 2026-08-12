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

BENCH = ROOT / "agent" / "benchmarks" / "v22-live-batch"
OUTPUT = ROOT / "runtime" / "v22-live-batch"
BLUEPRINTS = [BENCH / f"{index:03d}-blueprint.json" for index in range(1, 6)]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print(json.dumps({"ok": False, "stage": "configuration", "error": "OPENAI_API_KEY missing"}, ensure_ascii=False))
        return 2

    base_url = normalize_base_url(os.getenv("OPENAI_BASE_URL"))
    model = os.getenv("OPENAI_MODEL") or "gpt-5.4-mini"
    transport = make_responses_transport(base_url)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    cases: list[dict] = []
    for index, blueprint_path in enumerate(BLUEPRINTS, start=1):
        blueprint = _load(blueprint_path)
        packet = build_multistage_draft_packet(blueprint)
        case_id = f"{index:03d}"
        try:
            generated = generate_multistage_article(
                packet,
                model=model,
                api_key=api_key,
                transport=transport,
                timeout=240,
            )
        except GenerationError as exc:
            case_result = {
                "case_id": case_id,
                "article_id": blueprint.get("article_id"),
                "title": blueprint.get("title"),
                "generated": False,
                "approved": False,
                "error": str(exc),
            }
            cases.append(case_result)
            _write_json(OUTPUT / f"{case_id}-result.json", case_result)
            continue

        approval = evaluate_for_approval(packet, generated.article)
        multistage = evaluate_multistage(packet, generated.article)
        approved = approval.approved and multistage.passed
        case_result = {
            "case_id": case_id,
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
        cases.append(case_result)
        _write_json(OUTPUT / f"{case_id}-result.json", case_result)

    approved_count = sum(1 for item in cases if item.get("approved"))
    generated_count = sum(1 for item in cases if item.get("generated"))
    summary = {
        "ok": approved_count == len(BLUEPRINTS),
        "stage": "v22-live-batch-approval",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "model": model,
        "requested": len(BLUEPRINTS),
        "generated": generated_count,
        "approved": approved_count,
        "failed": len(BLUEPRINTS) - approved_count,
        "registry_write": False,
        "website_write": False,
        "scheduled": False,
        "published": False,
        "cases": [
            {
                key: item.get(key)
                for key in (
                    "case_id", "article_id", "title", "primary_keyword", "generated", "approved",
                    "quality_score", "editorial_score", "multistage_score", "response_id",
                    "approval_errors", "multistage_errors",
                )
            }
            for item in cases
        ],
    }
    _write_json(OUTPUT / "summary.json", summary)
    print("LIVE_BATCH_V22_JSON_START")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("LIVE_BATCH_V22_JSON_END")
    return 0 if summary["ok"] else 7


if __name__ == "__main__":
    raise SystemExit(main())
