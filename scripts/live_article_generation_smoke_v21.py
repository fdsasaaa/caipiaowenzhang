from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.ai_generation import GenerationError, generate_article
from engine.approval import evaluate_for_approval
from engine.draft_packets import build_draft_packet
from engine.provider_transport import make_responses_transport, normalize_base_url

BLUEPRINT = ROOT / "agent" / "results" / "v2-quality-smoke-001" / "blueprint.json"


def main() -> int:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print(json.dumps({"ok": False, "stage": "configuration", "error": "OPENAI_API_KEY missing"}, ensure_ascii=False))
        return 2
    base_url = normalize_base_url(os.getenv("OPENAI_BASE_URL"))
    model = os.getenv("OPENAI_MODEL") or "gpt-5.4-mini"

    blueprint = json.loads(BLUEPRINT.read_text(encoding="utf-8"))
    packet = build_draft_packet(blueprint)

    try:
        generated = generate_article(
            packet,
            model=model,
            api_key=api_key,
            transport=make_responses_transport(base_url),
            timeout=180,
        )
    except GenerationError as exc:
        print(json.dumps({
            "ok": False,
            "stage": "generation",
            "base_url": base_url,
            "model": model,
            "error": str(exc),
        }, ensure_ascii=False, indent=2))
        return 4

    approval = evaluate_for_approval(packet, generated.article)
    result = {
        "ok": approval.approved,
        "stage": "approval",
        "base_url": base_url,
        "model": generated.model,
        "response_id": generated.response_id,
        "approved": approval.approved,
        "status": approval.status,
        "quality_score": approval.quality_score,
        "editorial_score": approval.editorial_score,
        "errors": approval.errors,
        "warnings": approval.warnings,
        "article": generated.article,
        "approved_package": approval.publish_package,
    }
    print("LIVE_ARTICLE_SMOKE_JSON_START")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("LIVE_ARTICLE_SMOKE_JSON_END")
    return 0 if approval.approved else 7


if __name__ == "__main__":
    raise SystemExit(main())
