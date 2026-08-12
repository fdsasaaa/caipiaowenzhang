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
from .ai_generation_v22 import _normalize_multistage_article, build_multistage_generation_prompt
from .real_knowledge_evidence_normalization import normalize_real_knowledge_claim_metadata
from .real_knowledge_live_validation import normalize_real_knowledge_article


def build_real_knowledge_generation_prompt(packet: dict) -> str:
    contract = packet.get("real_knowledge_validation") or {}
    if not contract.get("validation_only"):
        raise GenerationError("real-knowledge validation contract missing")

    boundary = str(contract.get("required_source_parameter_boundary") or "")
    candidate_line = str(contract.get("required_final_candidate_line") or "")
    candidates = list(contract.get("final_candidates") or [])
    if not boundary or not candidate_line or not candidates:
        raise GenerationError("real-knowledge validation contract is incomplete")

    return build_multistage_generation_prompt(packet) + (
        "\n\n真实知识家族单篇验收合同（本轮只验证内容质量，不写库、不发布）：\n"
        "1. 本篇不是新的benchmark。technique_family/source_refs来自仓库中已登记的真实知识家族；"
        "但来源只支持‘采用哪些方法原子’这一层 provenance，不自动证明本次系统预设参数正确，更不证明预测优势。\n"
        "2. 下面这句来源/参数边界必须在正文中逐字出现，不得改写、缩短或把后半句删掉：\n"
        f"{boundary}\n"
        "3. 正文必须解释为什么后二是有序的00–99共100个结果；第一层严格按一大一小筛到50个、排除50个；"
        "第二层严格按一单一双从50个筛到26个、再排除24个；整体共排除74个。\n"
        "4. 不能只给数量。下面这句最终候选列表必须在正文中逐字出现，包含所有前导0，不得少号、多号、换号或改成省略号：\n"
        f"{candidate_line}\n"
        "5. 这26个值是固定条件下的确定性候选空间，不是推荐号码、命中率、胜率或下一期预测。"
        "正文要用普通人能理解的话说明这一点。\n"
        "6. practical_guidance.steps至少5步：固定后二位置→写出大小规则→执行大小层→执行单双层→核对26个候选并停止。"
        "stop_condition必须明确第二层完成后停止；新增任何条件必须另一次实验前先绑定规则/证据并冻结。\n"
        "7. 来源/参数边界句在claim_evidence中使用 source_claim + source_unverified + 实际source_refs；"
        "最终26候选句使用 calculation + verified_rule + 实际rule_refs。系统会对这两条确定性证据做规范化补全，"
        "但不会替你补正文；正文缺任何一条都应判失败。\n"
        "8. 不得写‘来源证明一大一小更好’、‘来源推荐一单一双’、‘筛到26个所以更容易中奖’等越界表述。\n"
        "9. 仍必须保留‘演示数据，不是真实开奖记录。’的安全披露。演示开奖号只用于解释，不参与预冻结参数选择。\n"
        "\n机器冻结的最终候选数组：\n"
        + json.dumps(candidates, ensure_ascii=False)
    )


def generate_real_knowledge_article(
    packet: dict,
    *,
    model: str,
    api_key: str,
    transport: Callable[[str, dict[str, str], dict, int], dict],
    timeout: int = 240,
) -> GenerationResult:
    if packet.get("contract_version") != "2.2-multistage":
        raise GenerationError("Draft Packet is not V2.2 multistage")
    if not packet.get("real_knowledge_validation", {}).get("validation_only"):
        raise GenerationError("Draft Packet is not locked for real-knowledge validation")

    payload = {
        "model": model,
        "store": False,
        "input": build_real_knowledge_generation_prompt(packet),
        "text": {
            "format": {
                "type": "json_schema",
                "name": "laocaimi_real_knowledge_article_v22",
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
    article = normalize_real_knowledge_article(packet, article)
    article = normalize_real_knowledge_claim_metadata(packet, article)
    validate_generated_identity(packet, article)
    return GenerationResult(
        article=article,
        provider="openai_compatible_real_knowledge_v22",
        model=model,
        response_id=response.get("id"),
    )
