from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.ai_generation import GenerationError, _response_output_text
from engine.provider_transport import models_endpoint, request_json, responses_endpoint

CHEAP_HINTS = ("nano", "mini", "flash", "small", "lite")


def _model_ids(payload: dict) -> list[str]:
    rows = payload.get("data") or []
    return [str(row.get("id")) for row in rows if isinstance(row, dict) and row.get("id")]


def _pick_model(models: list[str], requested: str | None) -> str:
    if requested:
        return requested
    for hint in CHEAP_HINTS:
        for model in models:
            if hint in model.lower():
                return model
    if models:
        return models[0]
    raise GenerationError("provider /models returned no usable model ids; pass --model explicitly")


def _structured_payload(model: str) -> dict:
    return {
        "model": model,
        "store": False,
        "max_output_tokens": 64,
        "input": "Return the single field ok with value ok. No other content.",
        "text": {
            "format": {
                "type": "json_schema",
                "name": "provider_preflight_v21",
                "strict": True,
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["ok"],
                    "properties": {"ok": {"type": "string", "enum": ["ok"]}},
                },
            }
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Low-cost V2.1 model-provider compatibility preflight")
    parser.add_argument("--base-url", default=os.getenv("OPENAI_BASE_URL"))
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL"))
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print(json.dumps({"ok": False, "stage": "credentials", "error": "OPENAI_API_KEY is required"}, ensure_ascii=False))
        return 2

    try:
        models_payload = request_json(models_endpoint(args.base_url), api_key=api_key, timeout=args.timeout)
        models = _model_ids(models_payload)
        model = _pick_model(models, args.model)
        response = request_json(
            responses_endpoint(args.base_url),
            api_key=api_key,
            payload=_structured_payload(model),
            timeout=args.timeout,
        )
        text = _response_output_text(response)
        parsed = json.loads(text)
        structured_ok = parsed == {"ok": "ok"}
        result = {
            "ok": structured_ok,
            "stage": "structured_responses",
            "base_url": args.base_url,
            "models_endpoint_ok": True,
            "model_count": len(models),
            "selected_model": model,
            "responses_endpoint_ok": True,
            "structured_output_ok": structured_ok,
            "response_id": response.get("id"),
            "usage": response.get("usage"),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if structured_ok else 5
    except (GenerationError, json.JSONDecodeError) as exc:
        # Never print credentials. GenerationError also redacts the active key from HTTP bodies.
        message = str(exc)
        message = re.sub(r"sk-[A-Za-z0-9_-]{12,}", "***REDACTED***", message)
        print(json.dumps({"ok": False, "stage": "provider_preflight", "error": message}, ensure_ascii=False, indent=2))
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
