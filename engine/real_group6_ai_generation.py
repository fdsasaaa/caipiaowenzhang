from __future__ import annotations

import json
from copy import deepcopy
from typing import Callable

from .ai_generation import (
    GenerationError,
    GenerationResult,
    _response_output_text,
    article_output_schema,
    validate_generated_identity,
)
from .real_group6_article_contract import build_real_group6_article_prompt
from .real_group6_evidence import normalize_real_group6_claim_metadata


def _group6_output_schema(packet: dict) -> dict:
    schema = deepcopy(article_output_schema(packet))
    support_enum = schema["properties"]["claim_evidence"]["items"]["properties"]["support_type"]["enum"]
    if "policy_contract" not in support_enum:
        support_enum.append("policy_contract")
    return schema


def generate_real_group6_article(
    packet: dict,
    *,
    model: str,
    api_key: str,
    transport: Callable[[str, dict[str, str], dict, int], dict],
    timeout: int = 300,
) -> GenerationResult:
    contract = packet.get("real_group6_validation") or {}
    binding = contract.get("binding") or {}
    if binding.get("group_mode") != "group6":
        raise GenerationError("group6 live contract mode changed")
    if binding.get("source_did_not_choose_mode") is not True:
        raise GenerationError("group6 live contract lost source/system provenance boundary")
    if contract.get("group6_unit_count") != 120:
        raise GenerationError("group6 unit count changed")
    if contract.get("target_play_full_domain_coverage") != 1.0:
        raise GenerationError("group6 target-domain coverage changed")
    if contract.get("full_domain_executable_portfolio_allowed") is not False:
        raise GenerationError("group6 full-domain execution unexpectedly allowed")
    if contract.get("normalized_bets_allowed") is not False:
        raise GenerationError("group6 validation unexpectedly allows normalized bets")

    payload = {
        "model": model,
        "store": False,
        "input": build_real_group6_article_prompt(),
        "text": {
            "format": {
                "type": "json_schema",
                "name": "laocaimi_real_family_group6_article_v2",
                "strict": True,
                "schema": _group6_output_schema(packet),
            }
        },
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = transport("https://api.openai.com/v1/responses", headers, payload, timeout)
    text = _response_output_text(response)
    try:
        article = json.loads(text)
    except json.JSONDecodeError as exc:
        raise GenerationError("structured group6 model output is not valid JSON") from exc
    if not isinstance(article, dict):
        raise GenerationError("structured group6 model output must be an object")

    article = normalize_real_group6_claim_metadata(packet, article)
    validate_generated_identity(packet, article)
    return GenerationResult(
        article=article,
        provider="openai_compatible_real_family_group6_v2",
        model=model,
        response_id=response.get("id"),
    )
