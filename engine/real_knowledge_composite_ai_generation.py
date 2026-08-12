from __future__ import annotations

import json
from typing import Callable

from .ai_generation import (
    GenerationError,
    GenerationResult,
    _response_output_text,
    article_output_schema,
    validate_generated_identity,
)
from .ai_generation_v22 import _normalize_multistage_article
from .real_knowledge_composite_article_contract import build_composite_article_prompt
from .real_knowledge_composite_evidence import normalize_composite_claim_metadata


def generate_composite_real_knowledge_article(
    packet: dict,
    *,
    model: str,
    api_key: str,
    transport: Callable[[str, dict[str, str], dict, int], dict],
    timeout: int = 300,
) -> GenerationResult:
    if packet.get("contract_version") != "2.2-multistage":
        raise GenerationError("Draft Packet is not V2.2 multistage")
    contract = packet.get("real_knowledge_composition") or {}
    if contract.get("final_candidate_count") != 534:
        raise GenerationError("composite article contract final count changed")
    if contract.get("must_list_all_final_candidates") is not False:
        raise GenerationError("composite article contract unexpectedly requires candidate dump")

    payload = {
        "model": model,
        "store": False,
        "input": build_composite_article_prompt(),
        "text": {
            "format": {
                "type": "json_schema",
                "name": "laocaimi_composite_real_knowledge_article_v22",
                "strict": True,
                "schema": article_output_schema(packet),
            }
        },
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = transport("https://api.openai.com/v1/responses", headers, payload, timeout)
    text = _response_output_text(response)
    try:
        article = json.loads(text)
    except json.JSONDecodeError as exc:
        raise GenerationError("structured model output is not valid JSON") from exc
    if not isinstance(article, dict):
        raise GenerationError("structured model output must be an object")

    article = _normalize_multistage_article(article, packet)
    article = normalize_composite_claim_metadata(packet, article)
    validate_generated_identity(packet, article)
    return GenerationResult(
        article=article,
        provider="openai_compatible_composite_real_knowledge_v22",
        model=model,
        response_id=response.get("id"),
    )
