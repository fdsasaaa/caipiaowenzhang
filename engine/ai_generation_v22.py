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
            f"排除 {stage.get('excluded_space')}；basis={stage.get('basis')}；"
            f"support_mode={stage.get('support_mode', 'verified_rule_calculation')}"
        )

    return base + (
        "\n\nV2.2 多层筛选合同（优先于V2.1关于‘没有第二过滤器就停止’的默认规则）：\n"
        "1. filter_pipeline_spec/filter_pipeline_result 是系统机器合同。阶段顺序、静态参数，以及样本型阶段的选择规则"
        "都在生成文章前固定；必须按给定顺序使用全部合同阶段，不得遗漏、换序或新增合同外阶段。\n"
        "2. 对 support_mode=verified_rule_calculation 的静态阶段，具体参数已由系统预冻结；"
        "对 support_mode=synthetic_case_calculation 的频率/冷热/遗漏阶段，只是 lookback/top_n/threshold 等选择规则预先冻结，"
        "具体数字池是系统从 Draft Packet 的演示数据确定性计算出来的，不得写成实验前已经知道，更不得写成来源推荐。\n"
        "3. 每一层正文都必须明确写出 before_space、after_space、excluded_space，并解释这一层具体怎么算。"
        "这些数字是候选空间的确定性计算，不是命中率或预测优势。\n"
        "4. basis=experimental_parameter 表示系统预先固定的研究参数；basis=synthetic_case_fixed_rule 表示规则预先固定、"
        "具体结果由演示样本计算。无论哪一种，都不得说它更容易中奖、更准、有效率更高，也不得伪造来源。\n"
        "5. practical_guidance.starting_space 写整个pipeline起点；after_primary_filter_space 写全部合同阶段完成后的最终空间。"
        "stop_condition 要明确：完成最后一层后停止；任何额外新过滤器必须另有已验证规则/证据并在下一次实验前冻结。\n"
        "6. 正文必须有清晰‘实际怎么操作/按步骤’章节，让读者能从起始空间逐层复算到最终候选空间。\n"
        "7. support_type=editorial 是非证据元数据，support_refs 必须是空数组 []。"
        "不要写 [\"rule_refs\"] 之类占位符；静态玩法/空间计算使用 verified_rule + 实际 rule_refs。\n"
        "8. support_mode=synthetic_case_calculation 的数字池、阶段空间和包含这些阶段的整体最终空间，"
        "必须使用 synthetic_case 且 support_refs 严格为 [\"case_bundle\"]。"
        "不要把演示样本计算升级成 verified_rule。\n"
        "9. 对来自演示开奖号、样本条数、样本和值/跨度/遗漏/频率的其他事实，同样必须使用 synthetic_case + [\"case_bundle\"]。\n"
        "10. 正文必须明确出现标准句‘演示数据，不是真实开奖记录。’。系统也会在模型漏写时确定性补入这句安全标签；"
        "该补入只改变披露标签，不改变任何玩法、参数、计算或结论。\n"
        "\n机器已验证的阶段：\n" + "\n".join(stage_lines) +
        f"\n整体：{result.get('starting_space')} -> {result.get('final_space')}，"
        f"总排除 {result.get('total_excluded')}。\n"
        "\n完整filter_pipeline_spec：\n" + json.dumps(spec, ensure_ascii=False, sort_keys=True) +
        "\n完整filter_pipeline_result：\n" + json.dumps(result, ensure_ascii=False, sort_keys=True)
    )


def _compact(value: object) -> str:
    return re.sub(r"\s+", "", str(value or ""))


def _stage_support(stage: dict, rules: list[str]) -> tuple[str, list[str]]:
    if stage.get("support_mode") == "synthetic_case_calculation":
        return "synthetic_case", ["case_bundle"]
    return "verified_rule", list(rules)


def _overall_support(result: dict, rules: list[str]) -> tuple[str, list[str]]:
    stages = result.get("stages") or []
    if any(stage.get("support_mode") == "synthetic_case_calculation" for stage in stages):
        return "synthetic_case", ["case_bundle"]
    return "verified_rule", list(rules)


def _matched_pipeline_support(packet: dict, claim: str) -> tuple[str, list[str]] | None:
    """Return the required evidence provenance for one pipeline calculation claim."""
    result = packet.get("practicality", {}).get("filter_pipeline_result") or {}
    rules = list(packet.get("immutable_facts", {}).get("rule_refs") or [])
    compact = _compact(claim)
    stages = result.get("stages", []) or []
    calculation_markers = (
        "筛到", "筛选", "继续筛", "排除", "候选", "空间", "缩到", "缩小",
        "得到", "剩下", "保留", "before", "after", "excluded", "->", "→",
    )

    matched_stages = []
    for stage in stages:
        before = str(stage.get("before_space"))
        after = str(stage.get("after_space"))
        excluded = str(stage.get("excluded_space"))
        if all(value not in {"None", ""} and value in compact for value in (before, after, excluded)):
            matched_stages.append(stage)

    if len(matched_stages) == 1 and any(marker in compact for marker in calculation_markers):
        return _stage_support(matched_stages[0], rules)

    start = str(result.get("starting_space"))
    final = str(result.get("final_space"))
    excluded = str(result.get("total_excluded"))
    overall_markers = ("整体", "总共", "合计", "最终", "全部完成", "完成后", "两层", "三层", "多层", "总排除")
    has_overall_marker = any(marker in compact for marker in overall_markers)

    if has_overall_marker and all(value not in {"None", ""} and value in compact for value in (start, final, excluded)):
        return _overall_support(result, rules)
    if has_overall_marker and all(value not in {"None", ""} and value in compact for value in (final, excluded)):
        if any(marker in compact for marker in ("最终", "总排除", "总共排除", "全部完成", "完成后")):
            return _overall_support(result, rules)
    return None


def _claim_matches_pipeline_result(packet: dict, claim: str) -> bool:
    """Backward-compatible predicate used by existing hardening tests."""
    return _matched_pipeline_support(packet, claim) is not None


def _pipeline_evidence_rows(packet: dict) -> list[dict]:
    """Build canonical evidence with provenance matching each pipeline stage."""
    result = packet.get("practicality", {}).get("filter_pipeline_result") or {}
    rules = list(packet.get("immutable_facts", {}).get("rule_refs") or [])
    rows: list[dict] = []
    for stage in result.get("stages", []) or []:
        support_type, support_refs = _stage_support(stage, rules)
        if support_type == "verified_rule" and not support_refs:
            continue
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
                "support_type": support_type,
                "support_refs": support_refs,
                "evidence_note": (
                    "系统按Draft Packet中已冻结的选择规则计算该层数字池；"
                    + ("具体数字来自演示数据，只证明确定性样本计算，不证明预测优势。" if support_type == "synthetic_case" else "只证明参数内容与数量，不证明预测优势。")
                ),
            })
        rows.append({
            "claim_text": (
                f"第{stage.get('index')}层候选空间从{stage.get('before_space')}个缩到"
                f"{stage.get('after_space')}个，排除{stage.get('excluded_space')}个。"
            ),
            "claim_type": "calculation",
            "support_type": support_type,
            "support_refs": support_refs,
            "evidence_note": (
                "系统依据Draft Packet中的合同阶段逐项枚举得到；"
                + ("该阶段包含演示样本衍生参数，因此证据归case_bundle；不证明预测优势。" if support_type == "synthetic_case" else "该阶段基于已验证玩法空间和系统预冻结静态参数；不证明预测优势。")
            ),
        })
        if result.get("space_type") == "unordered_2digit":
            rows.append({
                "claim_text": (
                    f"第{stage.get('index')}层候选空间从{stage.get('before_space')}注缩到"
                    f"{stage.get('after_space')}注，排除{stage.get('excluded_space')}注。"
                ),
                "claim_type": "calculation",
                "support_type": support_type,
                "support_refs": support_refs,
                "evidence_note": "系统对无序组选注数空间逐项枚举；证据类型跟随该阶段参数来源。",
            })
    if result:
        support_type, support_refs = _overall_support(result, rules)
        if support_type == "synthetic_case" or support_refs:
            rows.append({
                "claim_text": (
                    f"完整多层筛选从{result.get('starting_space')}个缩到{result.get('final_space')}个，"
                    f"总排除{result.get('total_excluded')}个。"
                ),
                "claim_type": "calculation",
                "support_type": support_type,
                "support_refs": support_refs,
                "evidence_note": "由系统汇总全部合同阶段的确定性候选空间结果；整体证据按最强依赖来源归类。",
            })
            if result.get("space_type") == "unordered_2digit":
                rows.append({
                    "claim_text": (
                        f"完整多层筛选从{result.get('starting_space')}注缩到{result.get('final_space')}注，"
                        f"总排除{result.get('total_excluded')}注。"
                    ),
                    "claim_type": "calculation",
                    "support_type": support_type,
                    "support_refs": support_refs,
                    "evidence_note": "由系统汇总无序组选全部合同阶段结果；证据类型跟随pipeline最强依赖来源。",
                })
    return rows


def _normalize_multistage_article(article: dict, packet: dict | None = None) -> dict:
    """Canonicalize non-evidentiary metadata and exact pipeline evidence provenance."""
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

        if isinstance(packet, dict) and entry.get("claim_type") == "calculation":
            required = _matched_pipeline_support(packet, str(entry.get("claim_text") or ""))
            if required is not None:
                required_type, required_refs = required
                if required_type == "verified_rule" and not required_refs:
                    continue
                if entry.get("support_type") != required_type or list(entry.get("support_refs") or []) != required_refs:
                    entry["support_type"] = required_type
                    entry["support_refs"] = required_refs
                    entry["evidence_note"] = (
                        str(entry.get("evidence_note") or "")
                        + f" [system-normalized: exact pipeline provenance -> {required_type}]"
                    ).strip()

    if isinstance(packet, dict):
        required_label = str(packet.get("output_contract", {}).get("must_include_case_label") or "").strip()
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
