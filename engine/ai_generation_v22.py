from __future__ import annotations

import json
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

    # Reuse every proven V2.1 instruction, but remove the compatibility-only
    # overall primary_filter_spec so the base prompt does not describe it as the
    # article's "only" filter. V2.2 instructions below own the multi-stage flow.
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
        "6. 候选空间数学事实登记为 calculation + verified_rule（引用Draft Packet rule_refs）。"
        "参数选择本身若只是experimental_parameter，不要伪装成verified_rule证明其预测效果。\n"
        "7. support_type=editorial 是非证据元数据，support_refs 必须是空数组 []。"
        "不要写 [\"rule_refs\"] 之类占位符；真实规则事实用 verified_rule + 实际 rule_refs。\n"
        "8. 对含‘注’的候选空间说明，至少为每组不同的数值关系建立一条 calculation evidence。"
        "同一组数字在正文步骤中重复解释可以复用同一数学证据，但不能完全没有对应 calculation。\n"
        "9. 正文必须明确出现标准句‘演示数据，不是真实开奖记录。’。系统也会在模型漏写时确定性补入这句安全标签；"
        "该补入只改变披露标签，不改变任何玩法、参数、计算或结论。\n"
        "\n机器已验证的阶段：\n" + "\n".join(stage_lines) +
        f"\n整体：{result.get('starting_space')} -> {result.get('final_space')}，"
        f"总排除 {result.get('total_excluded')}。\n"
        "\n完整filter_pipeline_spec：\n" + json.dumps(spec, ensure_ascii=False, sort_keys=True) +
        "\n完整filter_pipeline_result：\n" + json.dumps(result, ensure_ascii=False, sort_keys=True)
    )


def _normalize_multistage_article(article: dict, packet: dict | None = None) -> dict:
    """Canonicalize non-evidentiary metadata and mandatory synthetic disclosure.

    Two transformations are deliberately lossless with respect to factual
    content:
    1. editorial support_refs are removed because editorial rows are forbidden
       from proving hard claims;
    2. when a packet requires a synthetic-case disclosure and the model omits
       the decisive phrase, prepend the canonical disclosure sentence. This is
       a deterministic safety label derived from the packet, not model content.
    """
    normalized = deepcopy(article)
    entries = normalized.get("claim_evidence")
    if isinstance(entries, list):
        for entry in entries:
            if isinstance(entry, dict) and entry.get("support_type") == "editorial":
                entry["support_refs"] = []

    if isinstance(packet, dict):
        required_label = str(
            packet.get("output_contract", {}).get("must_include_case_label") or ""
        ).strip()
        content = str(normalized.get("content") or "")
        if required_label and required_label not in content:
            canonical = "演示数据，不是真实开奖记录。"
            normalized["content"] = f"<p><strong>{canonical}</strong></p>" + content
            if isinstance(entries, list):
                entries.append({
                    "claim_text": canonical,
                    "claim_type": "editorial",
                    "support_type": "synthetic_case",
                    "support_refs": ["case_bundle"],
                    "evidence_note": "系统按Draft Packet确定性补入强制演示数据披露标签；不改变正文事实或计算。",
                })
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
