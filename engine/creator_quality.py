from __future__ import annotations

from typing import Callable

from .creative_memory import (
    build_long_term_memory_snapshot,
    creator_memory_metadata,
    formal_inventory_duplicate_hits,
    select_style_dna,
)
from .creator_first import (
    CreatorFirstResult,
    build_creator_request,
    generate_creator_article,
)


def build_quality_creator_request(*, request_id: str | None = None, policy: dict | None = None) -> dict:
    request = build_creator_request(request_id=request_id, policy=policy)
    seed = request_id or request["article_id"]
    request["style_dna"] = select_style_dna(seed)
    request["long_term_memory"] = build_long_term_memory_snapshot()
    request["title_selection"] = {
        "internal_candidate_count": 5,
        "output_only_final_winner": True,
        "criteria": [
            "accurate to article content",
            "natural primary-keyword fit",
            "clear reader benefit or curiosity",
            "distinct from existing titles",
            "no exaggerated promise",
        ],
    }
    mandate = list(request.get("creative_mandate") or [])
    mandate.extend([
        "把 long_term_memory 当作长期创作记忆：避免重复已有核心技术、标题语义和表达套路，但绝不能照抄它们",
        "style_dna 只是本篇软性文风倾向，不是模板；可以自然偏离，不允许为了风格牺牲清晰度和玩法正确性",
        "定稿前在内部至少构思5个不同标题方向，并按 title_selection 选择一个最终标题；只输出最终胜出标题",
        "originality_note 必须说清本篇真正新的技术/解释/执行点是什么；仅仅更换参数不算创新",
        "优先创造新的关系、组合、迁移、反转、状态、资金纪律或解释方式，而不是对旧文章做同义改写",
    ])
    request["creative_mandate"] = mandate
    return request


def apply_quality_layer(result: CreatorFirstResult) -> CreatorFirstResult:
    package = result.approval.publish_package
    if package is not None:
        package.update(creator_memory_metadata(result.request, result.manifest))
        if result.approval.registry_record is not None:
            result.approval.registry_record.update(creator_memory_metadata(result.request, result.manifest))

    if result.approved and package is not None:
        hits = formal_inventory_duplicate_hits(package)
        if hits:
            first = hits[0]
            message = (
                "long-term formal inventory duplicate: "
                f"{first.get('article_id')} "
                f"(lexical={first.get('lexical'):.3f}, structural={first.get('structural'):.3f}; "
                f"reasons={','.join(first.get('reasons') or [])})"
            )
            result.errors = list(dict.fromkeys([*result.errors, message]))
            result.approval.errors = list(dict.fromkeys([*result.approval.errors, message]))
            result.approved = False
            result.approval.approved = False
            result.approval.status = "rejected_for_revision"
    return result


def generate_quality_creator_article(
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
    return apply_quality_layer(result)
