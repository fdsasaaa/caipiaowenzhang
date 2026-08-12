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


def _claim_schema() -> dict:
    return {
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


def _practical_guidance_schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "steps", "starting_space", "after_primary_filter_space",
            "parameter_freeze_rule", "stop_condition", "next_step_policy",
        ],
        "properties": {
            "steps": {"type": "array", "items": {"type": "string"}},
            "starting_space": {"type": "string"},
            "after_primary_filter_space": {"type": "string"},
            "parameter_freeze_rule": {"type": "string"},
            "stop_condition": {"type": "string"},
            "next_step_policy": {"type": "string"},
        },
    }


def article_output_schema(packet: dict | None = None) -> dict:
    required = [
        "article_id", "title", "seo_title", "slug", "meta_description", "primary_keyword",
        "secondary_keywords", "search_intent", "summary", "category", "site_category_key",
        "content_type", "content_format", "tags", "content", "rule_refs", "source_refs",
        "case_scope", "status", "generation_contract_version", "claim_evidence",
    ]
    properties = {
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
        "claim_evidence": {"type": "array", "items": _claim_schema()},
    }
    if packet and packet.get("editorial_contract_version"):
        required.extend(["editorial_contract_version", "practical_guidance"])
        properties["editorial_contract_version"] = {
            "type": "string", "enum": [str(packet["editorial_contract_version"])]
        }
        properties["practical_guidance"] = _practical_guidance_schema()
    return {
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": properties,
    }


def build_generation_prompt(packet: dict) -> str:
    editorial_rules = ""
    practicality = packet.get("practicality") or {}
    primary_filter_spec = practicality.get("primary_filter_spec") if isinstance(practicality, dict) else None
    if packet.get("editorial_contract_version"):
        editorial_rules = (
            "8. 这是V2.1实操质量合同：必须输出 practical_guidance，并在正文设置清晰的“实际怎么操作/操作步骤”类章节。\n"
            "9. practical_guidance.steps 至少4步；能计算候选空间时必须写明筛选前和主筛选后的规模，并解释到底筛掉多少。\n"
            "10. 参数必须先固定再看样本；没有第二条已验证规则或证据时，必须明确写出停止条件，不能为了显得更实用而临时拼第二过滤器。\n"
            "11. next_step_policy 必须说明：只有新增条件具有已验证规则/证据并可复算时，才允许继续缩小候选。\n"
        )
        if isinstance(primary_filter_spec, dict) and primary_filter_spec:
            editorial_rules += (
                "12. Draft Packet 已提供 practicality.primary_filter_spec。它是本篇唯一主筛选合同：必须原样使用其中的 selector/metric/参数，"
                "practical_guidance.starting_space 必须表达 starting_space，after_primary_filter_space 必须表达 after_filter_space，正文必须明确写出 excluded_space。"
                "绝不能把 case_bundle.sample_size 或演示样本条数当成理论候选空间。\n"
                "13. 如果 primary_filter_spec.basis 是 source_unverified_hypothesis，则只把该筛选参数写成“来源提到/来源声称、尚未独立验证的研究假设”；"
                "这类来源句的 support_type 必须是 source_unverified，并只引用 primary_filter_spec.support_ref。区间覆盖数量等可从已验证玩法机制复算的数学事实，"
                "可作为 calculation + verified_rule 登记，但不能把来源经验写成预测优势。\n"
            )

    facts = packet.get("immutable_facts") or {}
    display_term_rules = ""
    if str(facts.get("subject_lottery") or "") == "分分彩":
        display_term_rules = (
            "17. 本篇面向读者的彩种显示名统一优先使用‘分分彩’。title、seo_title、meta_description、primary_keyword、summary、tags和普通正文不要用‘时时彩’替代‘分分彩’。\n"
            "18. 如果采集来源原文里出现‘时时彩’，重写成文章时原则上改写为‘分分彩’，不要机械保留旧彩种词；案例文章同样优先使用‘分分彩’。"
            "只有在明确说明历史规则名、内部规则库分类、归档来源原文术语时，才允许少量保留‘时时彩’。\n"
            "19. 显示术语改写不得篡改 source_refs/rule_refs、原始来源存档或历史规则事实，也不得反过来声称原文原本使用了‘分分彩’。"
            "也就是说：读者显示层优先‘分分彩’，内部 mechanics/provenance 层保持真实原始术语。\n"
        )

    return (
        "你是老财迷内容引擎的受约束正文生成器。只根据下面 Draft Packet 写文章，不使用未提供的外部事实，"
        "不复制来源文章原文，不把来源声称升级为事实。输出必须严格符合给定 JSON Schema。\n\n"
        "硬规则：\n"
        "1. immutable_facts、SEO主词、rule_refs/source_refs、网站分类不可篡改。title 与 seo_title 应自然包含 exact primary_keyword；不要堆砌关键词。\n"
        "2. case_bundle 是演示数据时，正文必须明确标注指定的演示标签，不得写成真实开奖记录。所有来自 case_bundle 的样本条数、开奖号、和值、跨度、遗漏、频率等，support_type 必须是 synthetic_case，support_refs 必须严格等于 [\"case_bundle\"]，不能引用 BRBCW 来源或 rule_refs。\n"
        "3. mechanics_only 时不得陈述未核验的平台赔率、返点、奖金、收益等具体事实或数字。可以用一句免责声明说明“本文不讨论未核验的平台经济参数”，但不要展开任何具体值。\n"
        "4. 每一个规则/计算/来源声称/表现/经济/预测类硬声明，都要在 claim_evidence 中登记。\n"
        "5. verified_rule 只能引用 Draft Packet rule_refs；source_unverified 只能引用 source_refs，且正文必须明确使用“来源提到/原文声称/未验证”等限定。来源只负责说明经验从哪里来，不能替 synthetic case 作证。\n"
        "6. synthetic_case 只引用 case_bundle。演示标签可用 claim_type=editorial、support_type=synthetic_case；样本计算可用 claim_type=calculation、support_type=synthetic_case。即使句子写“演示数据，不是真实开奖记录”，support_refs 仍必须严格为 [\"case_bundle\"]。\n"
        "7. 文章用简单中文、短段落、HTML正文；禁止<script>/<iframe>/<form>/<object>/<embed>。\n"
        + editorial_rules
        + "14. 对正文中包含百分比、注数、命中率/准确率/成功率/胜率、赔率/返点/奖金/收益/利润/盈利或明确未来预测的每一个完整句子，claim_evidence.claim_text 必须复制该正文句子的完整文字（去掉HTML标签即可），不要改写成概括句。\n"
        "15. 同一数学事实如果在正文用不同句子重复出现，每个硬声明句都要分别登记；不能假设一条概括证据自动覆盖其他表述。\n"
        "16. 中文数字写法（如“三注”“百分之六”）与阿拉伯数字写法同样属于硬声明，不能通过换写法绕过证据登记。\n"
        + display_term_rules
        + "\nDraft Packet:\n" + json.dumps(packet, ensure_ascii=False, sort_keys=True)
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


def _check_response_state(response: dict) -> None:
    error = response.get("error")
    if error:
        message = error.get("message") if isinstance(error, dict) else str(error)
        raise GenerationError("model response error: " + str(message or "unknown error"))
    status = response.get("status")
    if status and status != "completed":
        details = response.get("incomplete_details") or {}
        raise GenerationError(f"model response not completed: status={status} details={details}")
    for item in response.get("output", []) or []:
        if item.get("type") != "message":
            continue
        for content in item.get("content", []) or []:
            if content.get("type") == "refusal":
                refusal = content.get("refusal") or content.get("text") or "model refused the request"
                raise GenerationError("model response refused: " + str(refusal)[:500])


def _response_output_text(response: dict) -> str:
    _check_response_state(response)
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
    if packet.get("editorial_contract_version"):
        expected["editorial_contract_version"] = packet.get("editorial_contract_version")
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
                "schema": article_output_schema(packet),
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