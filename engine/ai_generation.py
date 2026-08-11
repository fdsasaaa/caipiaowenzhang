from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable

RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5"


class GenerationError(RuntimeError):
    pass


@dataclass
class GenerationResult:
    article: dict
    provider: str
    model: str
    response_id: str | None = None


def article_output_schema() -> dict:
    claim_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["claim_text", "claim_type", "support_type", "support_refs", "evidence_note"],
        "properties": {
            "claim_text": {"type": "string"},
            "claim_type": {
                "type": "string",
                "enum": ["rule_fact", "calculation", "source_claim", "performance", "economics", "prediction", "editorial"],
            },
            "support_type": {
                "type": "string",
                "enum": ["verified_rule", "synthetic_case", "source_unverified", "editorial"],
            },
            "support_refs": {"type": "array", "items": {"type": "string"}},
            "evidence_note": {"type": "string"},
        },
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "article_id", "title", "seo_title", "slug", "meta_description", "primary_keyword",
            "secondary_keywords", "search_intent", "summary", "category", "site_category_key",
            "content_type", "content_format", "tags", "content", "rule_refs", "source_refs",
            "case_scope", "status", "generation_contract_version", "claim_evidence",
        ],
        "properties": {
            "article_id": {"type": "string"},
            "title": {"type": "string"},
            "seo_title": {"type": "string"},
            "slug": {"type": "string"},
            "meta_description": {"type": "string"},
            "primary_keyword": {"type": "string"},
            "secondary_keywords": {"type": "array", "items": {"type": "string"}},
            "search_intent": {"type": "string"},
            "summary": {"type": "string"},
            "category": {"type": "string"},
            "site_category_key": {"type": "string"},
            "content_type": {"type": "string"},
            "content_format": {"type": "string", "enum": ["html"]},
            "tags": {"type": "array", "items": {"type": "string"}},
            "content": {"type": "string"},
            "rule_refs": {"type": "array", "items": {"type": "string"}},
            "source_refs": {"type": "array", "items": {"type": "string"}},
            "case_scope": {"type": "string", "enum": ["mechanics_only", "economics"]},
            "status": {"type": "string", "enum": ["draft"]},
            "generation_contract_version": {"type": "string", "enum": ["2.0"]},
            "claim_evidence": {"type": "array", "items": claim_schema},
        },
    }


def build_generation_prompt(packet: dict) -> str:
    return (
        "你是老财迷内容引擎的受约束正文生成器。只根据下面 Draft Packet 写文章，不使用未提供的外部事实，"
        "不复制来源文章原文，不把来源声称升级为事实。输出必须严格符合给定 JSON Schema。\n\n"
        "硬规则：\n"
        "1. immutable_facts、SEO主词、rule_refs/source_refs、网站分类不可篡改。\n"
        "2. case_bundle 是演示数据时，正文必须明确标注指定的演示标签，不得写成真实开奖记录。\n"
        "3. mechanics_only 时不得陈述未核验的平台赔率、返点、奖金、收益。\n"
        "4. 每一个规则/计算/来源声称/表现/经济/预测类硬声明，都要在 claim_evidence 中登记。\n"
        "5. verified_rule 只能引用 Draft Packet rule_refs；source_unverified 只能引用 source_refs，且正文必须明确使用“来源提到/原文声称/未验证”等限定。\n"
        "6. synthetic_case 只引用 case_bundle，不能声称是真实开奖或实盘结果。\n"
        "7. 文章用简单中文、短段落、HTML正文；禁止<script>/<iframe>/<form>/<object>/<embed>。\n\n"
        "Draft Packet:\n" + json.dumps(packet, ensure_ascii=False, sort_keys=True)
    )


def _default_transport(url: str, headers: dict[str, str], payload: dict, timeout: int) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise GenerationError(f"model provider HTTP {exc.code}: {detail[:1000]}") from exc
    except OSError as exc:
        raise GenerationError(f"model provider transport failed: {exc}") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise GenerationError("model provider returned non-JSON response") from exc


def _response_output_text(response: dict) -> str:
    for item in response.get("output", []) or []:
        if item.get("type") != "message":
            continue
        for content in item.get("content", []) or []:
            if content.get("type") in {"output_text", "text"} and isinstance(content.get("text"), str):
                return content["text"]
    direct = response.get("output_text")
    if isinstance(direct, str):
        return direct
    raise GenerationError("model response contains no output_text")


def validate_generated_identity(packet: dict, article: dict) -> None:
    facts = packet.get("immutable_facts", {})
    seo = packet.get("seo", {})
    expected = {
        "article_id": packet.get("article_id"),
        "primary_keyword": seo.get("primary_keyword"),
        "search_intent": seo.get("search_intent"),
        "site_category_key": facts.get("site_category_key"),
        "content_type": facts.get("content_type"),
        "content_format": facts.get("content_format"),
        "rule_refs": facts.get("rule_refs", []),
        "source_refs": facts.get("source_refs", []),
        "case_scope": facts.get("case_scope"),
        "status": "draft",
        "generation_contract_version": "2.0",
    }
    errors = []
    for field, value in expected.items():
        if article.get(field) != value:
            errors.append(f"{field} differs from Draft Packet")
    if errors:
        raise GenerationError("generated article violated immutable contract: " + "; ".join(errors))


def generate_article(
    packet: dict,
    *,
    model: str | None = None,
    api_key: str | None = None,
    transport: Callable[[str, dict[str, str], dict, int], dict] | None = None,
    timeout: int = 120,
) -> GenerationResult:
    if packet.get("status") != "ready_for_ai_draft":
        raise GenerationError("Draft Packet is not ready_for_ai_draft")
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise GenerationError("OPENAI_API_KEY is required for real model generation")
    model = model or os.getenv("OPENAI_MODEL") or DEFAULT_MODEL
    payload = {
        "model": model,
        "store": False,
        "input": build_generation_prompt(packet),
        "text": {
            "format": {
                "type": "json_schema",
                "name": "laocaimi_article_draft_v2",
                "strict": True,
                "schema": article_output_schema(),
            }
        },
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = (transport or _default_transport)(RESPONSES_URL, headers, payload, timeout)
    text = _response_output_text(response)
    try:
        article = json.loads(text)
    except json.JSONDecodeError as exc:
        raise GenerationError("structured model output is not valid JSON") from exc
    if not isinstance(article, dict):
        raise GenerationError("structured model output must be an object")
    validate_generated_identity(packet, article)
    return GenerationResult(article=article, provider="openai_responses", model=model, response_id=response.get("id"))
