from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Callable

from .ai_generation import (
    GenerationError,
    GenerationResult,
    _response_output_text,
    article_output_schema,
    build_generation_prompt,
    validate_generated_identity,
)


def build_multistage_generation_prompt(packet: dict) -> str:
    practicality = packet.get("practicality") or {}
    result = practicality.get("filter_pipeline_result") or {}
    spec = practicality.get("filter_pipeline_spec") or {}

    prompt_packet = deepcopy(packet)
    prompt_packet.get("practicality", {}).pop("primary_filter_spec", None)
    base = build_generation_prompt(prompt_packet)

    stages = result.get("stages") or []
    stage_lines = []
    for stage in stages:
        stage_lines.append(
            f"- 第{stage.get('index')}层 {stage.get('label')}: "
            f"{stage.get('before_space')} -> {stage.get('after_space')}，"
            f"排除 {stage.get('excluded_space')}；basis={stage.get('basis')}"
        )

    return base + (
        "\n\nV2.2 多层筛选合同（优先于V2.1关于‘没有第二过滤器就停止’的默认规则）：\n"
        "1. filter_pipeline_spec/filter_pipeline_result 是系统在看到演示样本之前已经冻结并由机器枚举验证的合同，"
        "不是让模型临时发明过滤器。必须按给定顺序使用全部阶段，不得遗漏、换序或新增第三/第四层。\n"
        "2. 每一层正文都必须明确写出 before_space、after_space、excluded_space，并解释这一层具体怎么算。"
        "这些数字是候选空间的确定性计算，不是命中率或预测优势。\n"
        "3. basis=experimental_parameter 表示预先固定的研究/演示参数：可以用于确定性筛选，但不得说它更容易中奖、"
        "更准、有效率更高，也不得伪造来源。basis=source_unverified_hypothesis 才允许按source_ref转述来源，并必须明确未独立验证。\n"
        "4. practical_guidance.starting_space 写整个pipeline起点；after_primary_filter_space 写所有预冻结阶段完成后的最终空间。"
        "stop_condition 要明确：完成最后一层后停止；任何额外新过滤器必须另有已验证规则/证据并在下一次实验前冻结。\n"
        "5. 正文必须有清晰‘实际怎么操作/按步骤’章节，让读者能从起始空间逐层复算到最终候选空间。\n"
        "6. pipeline before/after/excluded 与过滤参数基数是系统自有机器事实，生成后系统会自动注入标准 calculation evidence。"
        "模型仍可解释这些数字，但不要把它们伪装成命中率或预测优势。\n"
        "7. support_type=editorial 是非证据元数据，support_refs 必须是空数组 []。"
        "不要写 [\"rule_refs\"] 之类占位符；真实规则事实用 verified_rule + 实际 rule_refs。\n"
        "8. 对来自演示开奖号、样本条数、样本和值/跨度/遗漏/频率的事实，仍必须使用 synthetic_case 且 support_refs 严格为 [\"case_bundle\"]。"
        "不要把机器pipeline空间计算和演示开奖样本计算混成同一种证据。\n"
        "9. 正文必须明确出现标准句‘演示数据，不是真实开奖记录。’。系统也会在模型漏写时确定性补入这句安全标签；"
        "该补入只改变披露标签，不改变任何玩法、参数、计算或结论。\n"
        "\n机器已验证的阶段：\n" + "\n".join(stage_lines) +
        f"\n整体：{result.get('starting_space')} -> {result.get('final_space')}，"
        f"总排除 {result.get('total_excluded')}。\n"
        "\n完整filter_pipeline_spec：\n" + json.dumps(spec, ensure_ascii=False, sort_keys=True) +
        "\n完整filter_pipeline_result：\n" + json.dumps(result, ensure_ascii=False, sort_keys=True)
    )


def _compact(value: object) -> str:
    return re.sub(r"\s+", "", str(value or ""))


def _claim_matches_pipeline_result(packet: dict, claim: str) -> bool:
    result = packet.get("practicality", {}).get("filter_pipeline_result") or {}
    compact = _compact(claim)
    for stage in result.get("stages", []) or []:
        before = str(stage.get("before_space"))
        after = str(stage.get("after_space"))
        excluded = str(stage.get("excluded_space"))
        label = _compact(stage.get("label"))
        stage_marker = f"第{stage.get('index')}层"
        if all(value in compact for value in (before, after, excluded)) and (
            (label and label in compact) or stage_marker in compact
        ):
            return True
    overall = (
        str(result.get("starting_space")),
        str(result.get("final_space")),
        str(result.get("total_excluded")),
    )
    if all(value not in {"None", ""} and value in compact for value in overall):
        if any(marker in compact for marker in ("整体", "总共", "合计", "最终", "两层")):
            return True
    return False


def _pipeline_evidence_rows(packet: dict) -> list[dict]:
    """Build canonical evidence for machine-enumerated V2.2 candidate spaces and fixed parameter cardinality."""
    result = packet.get("practicality", {}).get("filter_pipeline_result") or {}
    rules = list(packet.get("immutable_facts", {}).get("rule_refs") or [])
    if not rules:
        return []
    rows: list[dict] = []
    for stage in result.get("stages", []) or []:
        params = stage.get("params") or {}
        if stage.get("op") == "digit_pool" and isinstance(params.get("digits"), list):
            digits = list(params["digits"])
            rows.append({
                "claim_text": (
                    f"第{stage.get('index')}层候选数字池包含{len(digits)}个数字："
                    + "/".join(str(value) for value in digits)
                    + "。"
                ),
                "claim_type": "calculation",
                "support_type": "verified_rule",
                "support_refs": rules,
                "evidence_note": (
                    "系统直接读取Draft Packet中实验前已冻结的digit_pool参数并计算其基数；"
                    "只证明参数内容与数量，不证明预测优势。"
                ),
            })
        rows.append({
            "claim_text": (
                f"第{stage.get('index')}层候选空间从{stage.get('before_space')}个缩到"
                f"{stage.get('after_space')}个，排除{stage.get('excluded_space')}个。"
            ),
            "claim_type": "calculation",
            "support_type": "verified_rule",
            "support_refs": rules,
            "evidence_note": (
                "系统依据Draft Packet中已冻结的过滤参数与已验证玩法结果空间，"
                "通过filter_pipeline逐项枚举得到；此证据只证明候选空间数学，不证明预测优势。"
            ),
        })
        if result.get("space_type") == "unordered_2digit":
            rows.append({
                "claim_text": (
                    f"第{stage.get('index')}层候选空间从{stage.get('before_space')}注缩到"
                    f"{stage.get('after_space')}注，排除{stage.get('excluded_space')}注。"
                ),
                "claim_type": "calculation",
                "support_type": "verified_rule",
                "support_refs": rules,
                "evidence_note": (
                    "系统对无序组选注数空间逐项枚举；只证明固定过滤条件下的注数变化。"
                ),
            })
    if result:
        rows.append({
            "claim_text": (
                f"完整多层筛选从{result.get('starting_space')}个缩到{result.get('final_space')}个，"
                f"总排除{result.get('total_excluded')}个。"
            ),
            "claim_type": "calculation",
            "support_type": "verified_rule",
            "support_refs": rules,
            "evidence_note": "由系统汇总全部已冻结过滤阶段的确定性候选空间结果。",
        })
        if result.get("space_type") == "unordered_2digit":
            rows.append({
                "claim_text": (
                    f"完整多层筛选从{result.get('starting_space')}注缩到{result.get('final_space')}注，"
                    f"总排除{result.get('total_excluded')}注。"
                ),
                "claim_type": "calculation",
                "support_type": "verified_rule",
                "support_refs": rules,
                "evidence_note": "由系统汇总无序组选全部已冻结过滤阶段的确定性注数结果。",
            })
    return rows


def _normalize_multistage_article(article: dict, packet: dict | None = None) -> dict:
    """Canonicalize non-evidentiary metadata and system-owned V2.2 evidence."""
    normalized = deepcopy(article)
    entries = normalized.get("claim_evidence")
    if not isinstance(entries, list):
        entries = []
        normalized["claim_evidence"] = entries

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("support_type") == "editorial":
            entry["support_refs"] = []

        if isinstance(packet, dict):
            rules = list(packet.get("immutable_facts", {}).get("rule_refs") or [])
            claim_text = str(entry.get("claim_text") or "")
            is_pipeline_calculation = (
                entry.get("claim_type") == "calculation"
                and _claim_matches_pipeline_result(packet, claim_text)
            )

            # Some providers occasionally copy the prompt field name literally
            # and emit support_refs=["rule_refs"] instead of the packet's actual
            # rule IDs. Repair only machine-known pipeline calculations. A
            # placeholder on any non-pipeline claim remains invalid and is
            # rejected by the normal Claim→Evidence gate.
            if (
                is_pipeline_calculation
                and entry.get("support_type") == "verified_rule"
                and entry.get("support_refs") == ["rule_refs"]
                and rules
            ):
                entry["support_refs"] = rules
                entry["evidence_note"] = (
                    str(entry.get("evidence_note") or "")
                    + " [system-normalized: exact pipeline rule_refs placeholder]"
                ).strip()

            if (
                is_pipeline_calculation
                and entry.get("support_type") == "synthetic_case"
                and rules
            ):
                entry["support_type"] = "verified_rule"
                entry["support_refs"] = rules
                entry["evidence_note"] = (
                    str(entry.get("evidence_note") or "")
                    + " [system-normalized: machine filter_pipeline calculation]"
                ).strip()

    if isinstance(packet, dict):
        required_label = str(
            packet.get("output_contract", {}).get("must_include_case_label") or ""
        ).strip()
        content = str(normalized.get("content") or "")
        if required_label and required_label not in content:
            canonical = "演示数据，不是真实开奖记录。"
            normalized["content"] = f"<p><strong>{canonical}</strong></p>" + content
            entries.append({
                "claim_text": canonical,
                "claim_type": "editorial",
                "support_type": "synthetic_case",
                "support_refs": ["case_bundle"],
                "evidence_note": "系统按Draft Packet确定性补入强制演示数据披露标签；不改变正文事实或计算。",
            })

        existing = {
            (
                str(entry.get("claim_text") or ""),
                str(entry.get("support_type") or ""),
                tuple(entry.get("support_refs") or []),
            )
            for entry in entries if isinstance(entry, dict)
        }
        for row in _pipeline_evidence_rows(packet):
            key = (row["claim_text"], row["support_type"], tuple(row["support_refs"]))
            if key not in existing:
                entries.append(row)
                existing.add(key)
    return normalized


def generate_multistage_article(
    packet: dict,
    *,
    model: str,
    api_key: str,
    transport: Callable[[str, dict[str, str], dict, int], dict],
    timeout: int = 180,
) -> GenerationResult:
    if packet.get("contract_version") != "2.2-multistage":
        raise GenerationError("Draft Packet is not V2.2 multistage")
    payload = {
        "model": model,
        "store": False,
        "input": build_multistage_generation_prompt(packet),
        "text": {
            "format": {
                "type": "json_schema",
                "name": "laocaimi_article_draft_v22_multistage",
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
    validate_generated_identity(packet, article)
    return GenerationResult(
        article=article,
        provider="openai_compatible_responses_v22",
        model=model,
        response_id=response.get("id"),
    )
