from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .ai_generation import RESPONSES_URL, _response_output_text, article_output_schema
from .approval import ApprovalResult, evaluate_for_approval
from .creator_style import CreatorStyleReport, evaluate_creator_style
from .rules import load_rules
from .site_contract import required_content_format, site_category_for
from .store import ROOT, iter_registry

POLICY_PATH = ROOT / "policies" / "CREATOR_FIRST.json"


class CreatorFirstError(ValueError):
    pass


@dataclass
class CreatorFirstResult:
    request: dict
    manifest: dict
    article: dict
    packet: dict
    approval: ApprovalResult
    style: CreatorStyleReport
    approved: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    response_id: str | None = None


def load_creator_policy(path: Path | None = None) -> dict:
    path = path or POLICY_PATH
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or int(data.get("version") or 0) < 1:
        raise CreatorFirstError("invalid creator-first policy")
    if data.get("mode") != "creator_first":
        raise CreatorFirstError("creator-first policy mode changed")
    return data


def _effective_article_memory(limit: int) -> list[dict]:
    latest: dict[str, dict] = {}
    order: list[str] = []
    for row in iter_registry("articles"):
        article_id = str(row.get("article_id") or "")
        if not article_id:
            continue
        if article_id not in latest:
            order.append(article_id)
        latest[article_id] = dict(row)
    active = []
    for article_id in reversed(order):
        row = latest[article_id]
        if str(row.get("status") or "") not in {"approved", "queued", "scheduled", "published", "draft", "idea"}:
            continue
        active.append({
            "article_id": article_id,
            "title": row.get("title"),
            "primary_keyword": row.get("primary_keyword"),
            "subject_lottery": row.get("subject_lottery") or row.get("lottery"),
            "subject_play": row.get("subject_play") or row.get("play"),
            "technique_atoms": row.get("technique_atoms", []),
            "information_gain_type": row.get("information_gain_type"),
        })
        if len(active) >= limit:
            break
    return active


def verified_mechanics_catalog(policy: dict | None = None) -> list[dict]:
    policy = policy or load_creator_policy()
    aliases = policy.get("public_subject_aliases", {})
    rows: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for rule in load_rules():
        if rule.get("status") != "verified" or rule.get("scope", "full") not in {"mechanics", "full"}:
            continue
        rule_id = str(rule.get("rule_id") or "").strip()
        lottery = str(rule.get("lottery") or "").strip()
        play = str(rule.get("play") or "").strip()
        if not rule_id or not lottery or not play:
            continue
        key = (rule_id, lottery, play)
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            "rule_ref": rule_id,
            "internal_lottery": lottery,
            "reader_lottery": str(aliases.get(lottery, lottery)),
            "play": play,
        })
    return sorted(rows, key=lambda row: (row["reader_lottery"], row["play"], row["rule_ref"]))


def build_creator_request(*, request_id: str | None = None, policy: dict | None = None) -> dict:
    policy = policy or load_creator_policy()
    token = request_id or uuid.uuid4().hex[:16]
    article_id = "LCM-CREATOR-" + token
    return {
        "creator_contract_version": "1.0",
        "article_id": article_id,
        "available_mechanics": verified_mechanics_catalog(policy),
        "existing_article_memory": _effective_article_memory(int(policy.get("max_memory_articles") or 80)),
        "creative_mandate": list(policy.get("creative_mandate") or []),
        "hard_gates": list(policy.get("hard_gates") or []),
        "economics_policy": dict(policy.get("economics_policy") or {}),
        "draw_data_available": False,
        "automatic_retry": False,
        "website_sync": False,
        "scheduled": False,
        "published": False,
    }


def _manifest_schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "selected_rule_ref", "subject_lottery", "subject_play", "creation_mode",
            "technique_name", "technique_tags", "originality_note", "reader_value",
            "uses_draw_data", "uses_bankroll_design", "uses_staking_design",
            "bankroll_design_summary", "staking_design_summary", "case_label", "case_notes",
        ],
        "properties": {
            "selected_rule_ref": {"type": "string"},
            "subject_lottery": {"type": "string"},
            "subject_play": {"type": "string"},
            "creation_mode": {
                "type": "string",
                "enum": ["technique", "data_research", "bankroll", "staking", "hybrid"],
            },
            "technique_name": {"type": "string"},
            "technique_tags": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 8},
            "originality_note": {"type": "string"},
            "reader_value": {"type": "string"},
            "uses_draw_data": {"type": "boolean"},
            "uses_bankroll_design": {"type": "boolean"},
            "uses_staking_design": {"type": "boolean"},
            "bankroll_design_summary": {"type": "string"},
            "staking_design_summary": {"type": "string"},
            "case_label": {"type": "string"},
            "case_notes": {"type": "array", "items": {"type": "string"}, "maxItems": 20},
        },
    }


def creator_output_schema(request: dict) -> dict:
    article_schema = article_output_schema(None)
    article_schema = json.loads(json.dumps(article_schema))
    article_schema["properties"]["article_id"] = {"type": "string", "enum": [request["article_id"]]}
    article_schema["properties"]["case_scope"] = {"type": "string", "enum": ["mechanics_only"]}
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["manifest", "article"],
        "properties": {
            "manifest": _manifest_schema(),
            "article": article_schema,
        },
    }


def build_creator_prompt(request: dict) -> str:
    return (
        "你是老财迷彩票内容项目的核心创作者，不是批量模板填充器。你的任务是自由创造一篇真正不同、讲得通、"
        "普通读者愿意看完的彩票技巧文章。系统不替你指定技巧角度；你自己选择玩法、技术思路、案例表达，"
        "也可以设计资金管理或倍投研究，但必须服从下面少量硬规则。\n\n"
        "创作原则：\n"
        "1. 从 available_mechanics 里自主选择一个已验证玩法；selected_rule_ref 必须来自该清单。\n"
        "2. existing_article_memory 只是长期记忆，用来避免重复，不是模板库。不要模仿旧标题、旧结构或旧套路。\n"
        "3. 技巧可以是你自己创造的、多个常识组合出的、数据观察型的、资金管理型的、倍投型的或混合型的；"
        "但不能把一个历史现象包装成未来预测优势。\n"
        "4. 默认 mechanics_only。没有已核验的平台奖金/赔率/返点时，资金和倍投设计优先用相对单位、本金暴露、"
        "停止条件和风险路径说明，不写固定盈利承诺。\n"
        "5. 如果用了自拟号码、统计样本或计算演示，manifest.case_label 必须写清它是演示案例，正文逐字出现该标签；"
        "相应数字声明在 claim_evidence 中使用 synthetic_case + [\"case_bundle\"]。如果没有演示数字，case_label 可以为空。\n"
        "6. 玩法事实只由 selected_rule_ref 支持；你原创的投注技巧只是研究设计，不能写成官方规则、来源结论或已证明优势。\n"
        "7. 面向读者尽量使用‘分分彩’而不是‘时时彩’；内部规则名不用出现在普通正文。\n"
        "8. 文案要简约、明了、人性化：短段落、少标题、直接讲方法和例子。不要出现 Draft Packet、Blueprint、Angle、"
        "claim_evidence、system_research、机器合同等工程词。不要写成流水线报告。\n"
        "9. SEO自然完成：标题和主关键词贴合真实搜索意图，但不要堆关键词。\n"
        "10. 一次只创造这一篇，不自动重试，不为了通过审核而降低规则。\n\n"
        "你可以把已有1000+文章和来源知识看成经验库，但创作决策由你完成。目标是长期创造大量不同玩法、不同技术、"
        "不同设计思路的文章，而不是把有限候选池填满。\n\n"
        "当前请求：\n"
        + json.dumps(request, ensure_ascii=False, indent=2)
        + "\n\n严格按 JSON Schema 输出 manifest + article。"
    )


def _selected_mechanic(request: dict, manifest: dict) -> dict:
    selected = str(manifest.get("selected_rule_ref") or "")
    matches = [row for row in request.get("available_mechanics", []) if row.get("rule_ref") == selected]
    if len(matches) != 1:
        raise CreatorFirstError("selected_rule_ref is not exactly one verified mechanic from this creator request")
    return matches[0]


def build_creator_packet(request: dict, manifest: dict, article: dict) -> dict:
    mechanic = _selected_mechanic(request, manifest)
    expected_subject = mechanic["reader_lottery"]
    if manifest.get("subject_lottery") != expected_subject:
        raise CreatorFirstError("manifest subject_lottery does not match selected verified mechanic")
    if manifest.get("subject_play") != mechanic["play"]:
        raise CreatorFirstError("manifest subject_play does not match selected verified mechanic")
    if article.get("article_id") != request.get("article_id"):
        raise CreatorFirstError("article_id changed from creator request")
    if article.get("rule_refs") != [mechanic["rule_ref"]]:
        raise CreatorFirstError("article rule_refs must contain only selected_rule_ref")
    if article.get("source_refs") not in ([], None):
        raise CreatorFirstError("creator-first original article must not invent source_refs")
    if article.get("case_scope") != "mechanics_only":
        raise CreatorFirstError("creator-first V1 defaults to mechanics_only")
    if manifest.get("uses_draw_data") is True and not request.get("draw_data_available"):
        raise CreatorFirstError("creator-first V1 cannot claim draw-data use when no draw data was supplied")

    case_label = str(manifest.get("case_label") or "").strip()
    synthetic_entries = [
        row for row in (article.get("claim_evidence") or [])
        if isinstance(row, dict) and row.get("support_type") == "synthetic_case"
    ]
    if synthetic_entries and not case_label:
        raise CreatorFirstError("synthetic_case evidence requires a visible creator case_label")
    if case_label and case_label not in str(article.get("content") or ""):
        raise CreatorFirstError("creator case_label is missing from article content")

    technique_tags = [str(value).strip() for value in manifest.get("technique_tags", []) if str(value).strip()]
    seed = json.dumps({
        "article_id": request["article_id"],
        "rule_ref": mechanic["rule_ref"],
        "mode": manifest.get("creation_mode"),
        "technique": manifest.get("technique_name"),
        "tags": technique_tags,
    }, ensure_ascii=False, sort_keys=True)
    fingerprint = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    content_type = "technique_article"
    site_category_key = site_category_for(content_type)
    content_format = required_content_format()
    required_fields = [
        "article_id", "title", "seo_title", "slug", "meta_description", "primary_keyword",
        "secondary_keywords", "search_intent", "summary", "category", "site_category_key",
        "content_type", "content_format", "tags", "content", "rule_refs", "source_refs",
        "case_scope", "status", "generation_contract_version", "claim_evidence",
    ]
    return {
        "packet_id": "CFDP-" + fingerprint[:16],
        "article_id": request["article_id"],
        "blueprint_id": "CREATOR-FIRST-" + fingerprint[:16],
        "status": "ready_for_ai_draft",
        "immutable_facts": {
            "provider_id": None,
            "lottery": mechanic["internal_lottery"],
            "play": mechanic["play"],
            "subject_lottery": expected_subject,
            "subject_play": mechanic["play"],
            "content_type": content_type,
            "site_category_key": site_category_key,
            "content_format": content_format,
            "technique_family": "creator_first_original",
            "technique_atoms": technique_tags,
            "rule_refs": [mechanic["rule_ref"]],
            "source_refs": [],
            "case_scope": "mechanics_only",
            "fingerprint": fingerprint,
            "case_structure": (
                f"creator_first;mode={manifest.get('creation_mode')};"
                f"technique={manifest.get('technique_name')};play={mechanic['play']}"
            ),
            "information_gain_type": "creator_original",
            "angle_signature": None,
            "article_angle_contract_version": None,
            "angle_contract_verified": False,
        },
        "seo": {
            "title": article.get("title"),
            "slug_seed": article.get("slug"),
            "primary_keyword": article.get("primary_keyword"),
            "secondary_keywords": article.get("secondary_keywords", []),
            "search_intent": article.get("search_intent"),
            "meta_description": article.get("meta_description"),
        },
        "style": {
            "language": "zh-CN",
            "plain_chinese": True,
            "short_paragraphs": True,
            "avoid_empty_intro": True,
            "tone": "human_clear_concise",
            "content_format": content_format,
        },
        "outline": [],
        "case_bundle": {
            "case_type": "creator_first_self_authored_example",
            "must_label_as": case_label,
            "notes": list(manifest.get("case_notes") or []),
        },
        "claims": {
            "allowed": [
                "explain verified gameplay mechanics",
                "present original technique design as a research/example method",
                "use self-authored examples when clearly labeled",
                "discuss bankroll/staking structure without profit guarantees",
            ],
            "forbidden_terms": ["稳赚", "必中", "包赢", "必赚", "百分百中奖", "100%中奖", "无风险"],
            "economics_allowed": False,
            "unverified_hit_rate_as_fact": False,
            "historical_pattern_as_future_guarantee": False,
        },
        "compliance": {
            "policy_ref": "USER-BET-COMPLIANCE-90-V1",
            "normalized_bets_required_for_executable_bet_examples": True,
            "export_requires_pass": True,
        },
        "source_use": {
            "paraphrase_required": True,
            "copy_source_article_verbatim": False,
            "source_claims_must_remain_unverified_unless_rule_refs_support_them": True,
        },
        "output_contract": {
            "required_fields": required_fields,
            "status_after_generation": "draft",
            "must_include_case_label": case_label or None,
        },
        "creator_manifest": dict(manifest),
        "creator_first_contract_version": request["creator_contract_version"],
    }


def validate_creator_output(request: dict, payload: dict) -> CreatorFirstResult:
    if not isinstance(payload, dict) or not isinstance(payload.get("manifest"), dict) or not isinstance(payload.get("article"), dict):
        raise CreatorFirstError("creator output must contain manifest and article objects")
    manifest = dict(payload["manifest"])
    article = dict(payload["article"])
    packet = build_creator_packet(request, manifest, article)
    approval = evaluate_for_approval(packet, article)
    style = evaluate_creator_style(article)
    errors = list(dict.fromkeys([*approval.errors, *style.errors]))
    warnings = list(dict.fromkeys([*approval.warnings, *style.warnings]))
    return CreatorFirstResult(
        request=request,
        manifest=manifest,
        article=article,
        packet=packet,
        approval=approval,
        style=style,
        approved=approval.approved and style.passed,
        errors=errors,
        warnings=warnings,
        response_id=article.get("provider_response_id"),
    )


def generate_creator_article(
    request: dict,
    *,
    model: str,
    api_key: str,
    transport: Callable[[str, dict[str, str], dict, int], dict],
    timeout: int = 300,
) -> CreatorFirstResult:
    payload = {
        "model": model,
        "store": False,
        "input": build_creator_prompt(request),
        "text": {
            "format": {
                "type": "json_schema",
                "name": "laocaimi_creator_first_v1",
                "strict": True,
                "schema": creator_output_schema(request),
            }
        },
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = transport(RESPONSES_URL, headers, payload, timeout)
    text = _response_output_text(response)
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CreatorFirstError("creator structured output is not valid JSON") from exc
    if not isinstance(value, dict):
        raise CreatorFirstError("creator structured output must be an object")
    article = value.get("article")
    if not isinstance(article, dict):
        raise CreatorFirstError("creator structured output missing article")
    if response.get("id"):
        article["provider_response_id"] = response.get("id")
    result = validate_creator_output(request, value)
    result.response_id = response.get("id")
    return result
