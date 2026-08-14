from __future__ import annotations

from typing import Callable

from .creator_first import CreatorFirstResult
from .creator_quality import (
    apply_quality_layer,
    build_quality_creator_request,
)
from .creator_first import generate_creator_article
from .draw_research import build_draw_research_context


def build_history_research_creator_request(
    dataset: dict,
    *,
    request_id: str | None = None,
    policy: dict | None = None,
) -> dict:
    request = build_quality_creator_request(request_id=request_id, policy=policy)
    context = build_draw_research_context(dataset)
    request["draw_data_available"] = True
    request["draw_research_context"] = context
    request["draw_research_mode"] = "idea_only_v1.2"

    mandate = list(request.get("creative_mandate") or [])
    mandate.extend([
        "可以使用 draw_research_context 观察历史结构、发现关系并提出新的投注技巧假设，但它只是一层私有研究输入",
        "历史数据首先服务于‘想出新的研究角度’，不是让文章声称某个模式未来更容易出现",
        "V1.2没有公开 historical-evidence 通道：最终正文不得引用 draw_research_context 中的历史频数、比例、命中率或样本表现作为事实",
        "如果数据启发了一个新技巧，请把它抽象成清晰、可复算的结构规则，并用 synthetic_case 自拟案例解释",
        "禁止在同一历史样本上不断更换参数直到得到漂亮结果；不要把样本内筛选包装成优势",
        "manifest.uses_draw_data 必须如实表示本篇是否实际使用了这份研究输入",
    ])
    request["creative_mandate"] = mandate
    return request


def apply_history_research_layer(result: CreatorFirstResult) -> CreatorFirstResult:
    result = apply_quality_layer(result)
    context = result.request.get("draw_research_context") or {}
    uses_draw = result.manifest.get("uses_draw_data") is True

    if uses_draw and not context:
        message = "manifest uses_draw_data=true but no verified draw_research_context is attached"
        result.errors = list(dict.fromkeys([*result.errors, message]))
        result.approval.errors = list(dict.fromkeys([*result.approval.errors, message]))
        result.approved = False
        result.approval.approved = False
        result.approval.status = "rejected_for_revision"
        return result

    if context and result.approval.publish_package is not None:
        metadata = {
            "creator_research_mode": "idea_only_v1.2",
            "creator_research_dataset_id": context.get("dataset_id"),
            "creator_research_dataset_hash": context.get("dataset_hash"),
            "creator_research_record_count": context.get("record_count"),
            "creator_used_draw_research": uses_draw,
        }
        result.approval.publish_package.update(metadata)
        if result.approval.registry_record is not None:
            result.approval.registry_record.update(metadata)
    return result


def generate_history_research_creator_article(
    request: dict,
    *,
    model: str,
    api_key: str,
    transport: Callable[[str, dict[str, str], dict, int], dict],
    timeout: int = 300,
) -> CreatorFirstResult:
    result = generate_creator_article(
        request,
        model=model,
        api_key=api_key,
        transport=transport,
        timeout=timeout,
    )
    return apply_history_research_layer(result)
