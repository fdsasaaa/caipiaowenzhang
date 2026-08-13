from __future__ import annotations

import copy
import hashlib
from typing import Iterable

ANGLE_CONTRACT_VERSION = "1.0"
AUDITED_ANGLE_STRUCTURAL_WEIGHT = 0.20

ANGLE_TYPES = (
    "mechanics_case",
    "space_math",
    "execution_checklist",
    "parameter_boundary",
    "multistage_order",
    "sample_provenance",
)

ANGLE_KEYWORD_SUFFIX = {
    "mechanics_case": "技巧",
    "space_math": "注数计算",
    "execution_checklist": "筛选步骤",
    "parameter_boundary": "参数设置",
    "multistage_order": "筛选顺序",
    "sample_provenance": "演示案例",
}

_ACTIVE_FORMAL_STATUSES = {"approved", "queued", "scheduled", "published"}


def _pipeline_result(blueprint: dict) -> dict:
    return dict((blueprint.get("production_filter_contract") or {}).get("filter_pipeline_result") or {})


def _stages(blueprint: dict) -> list[dict]:
    return list(_pipeline_result(blueprint).get("stages") or [])


def _is_sample_stage(stage: dict) -> bool:
    return str(stage.get("support_mode") or "") == "synthetic_case_calculation"


def _keyword_stem(primary_keyword: object) -> str:
    value = str(primary_keyword or "").strip()
    return value[:-2] if value.endswith("技巧") else value


def _stage_label(stage: dict) -> str:
    return str(stage.get("label") or stage.get("atom") or "").strip()


def _stage_parameter_signature(stage: dict) -> str:
    params = stage.get("params") or {}
    values: list[str] = []
    for key in (
        "min", "max", "odd_count", "big_count", "has_repeat", "pair_difference",
        "lookback", "top_n", "threshold",
    ):
        if key in params:
            values.append(f"{key}={params[key]}")
    mode = "sample" if _is_sample_stage(stage) else "static"
    return (
        f"{stage.get('atom')}[{','.join(values)}/{mode}]"
        f":{stage.get('before_space')}->{stage.get('after_space')}"
    )


def _pipeline_signature(blueprint: dict) -> str:
    return ">".join(_stage_parameter_signature(stage) for stage in _stages(blueprint))


def _pipeline_counts(blueprint: dict) -> tuple[int, int, int, int]:
    result = _pipeline_result(blueprint)
    return (
        int(result.get("starting_space") or 0),
        int(result.get("final_space") or 0),
        int(result.get("total_excluded") or 0),
        int(result.get("stage_count") or len(result.get("stages") or [])),
    )


def _evidence_mode(blueprint: dict) -> str:
    sample_count = sum(1 for stage in _stages(blueprint) if _is_sample_stage(stage))
    if sample_count == 0:
        return "static_only"
    if sample_count == len(_stages(blueprint)):
        return "sample_only"
    return "mixed"


def allowed_angle_types(blueprint: dict) -> list[str]:
    stages = _stages(blueprint)
    if not stages:
        return []
    values = ["mechanics_case", "space_math", "execution_checklist", "parameter_boundary"]
    if len(stages) >= 2:
        values.append("multistage_order")
    if any(_is_sample_stage(stage) for stage in stages):
        values.append("sample_provenance")
    return values


def angle_primary_keyword(blueprint: dict, angle_type: str) -> str:
    if angle_type not in ANGLE_KEYWORD_SUFFIX:
        raise ValueError(f"unsupported article angle: {angle_type}")
    return _keyword_stem(blueprint.get("primary_keyword")) + ANGLE_KEYWORD_SUFFIX[angle_type]


def _angle_identity_text(blueprint: dict, angle_type: str, primary_keyword: str) -> tuple[str, str, str]:
    stages = _stages(blueprint)
    stage_count = len(stages)
    chain = "→".join(_stage_label(stage) for stage in stages)
    start, final, excluded, _ = _pipeline_counts(blueprint)
    play = str(blueprint.get("subject_play") or blueprint.get("play") or "玩法")
    sample_stages = [stage for stage in stages if _is_sample_stage(stage)]

    if angle_type == "mechanics_case":
        return (
            f"{primary_keyword}：{chain}具体怎么算，用完整案例从{start}复算到{final}",
            f"理解{play}里{chain}分别计算什么，并用固定演示案例完整复算一次",
            f"用简单中文解释{chain}的机制，并完成从{start}到{final}的可复算案例。",
        )
    if angle_type == "space_math":
        return (
            f"{primary_keyword}：{start}个候选为什么变成{final}个，排除{excluded}个怎么算",
            f"核对{play}的候选空间计算，逐项确认{start}到{final}以及排除{excluded}个的确定性结果",
            f"把候选空间的确定性数学过程算清楚：起点{start}、终点{final}、排除{excluded}。",
        )
    if angle_type == "execution_checklist":
        return (
            f"{primary_keyword}：实际操作按哪几步做，筛到{final}个后什么时候必须停止",
            f"按固定顺序执行{chain}，检查参数、候选空间和停止条件，形成可重复的人工操作清单",
            "把机器合同改写成可执行清单，读者能照步骤复算并知道何时停止。",
        )
    if angle_type == "parameter_boundary":
        if sample_stages:
            title = f"{primary_keyword}：哪些规则先冻结，哪些数字池只能由演示样本算出来"
            intent = f"区分{play}中生成前冻结的选择规则与演示样本确定性算出的具体数字池，避免把样本结果写成来源推荐"
            goal = "解释参数归属边界：规则先冻结，样本型具体结果由演示数据计算，来源不得替系统参数背书。"
        else:
            title = f"{primary_keyword}：哪些参数是系统研究预设，为什么不能写成来源推荐"
            intent = f"区分{play}中的系统研究预设参数与来源经验，明确具体参数不是原文推荐也不证明预测优势"
            goal = "解释静态参数归属边界：系统研究预设不等于来源推荐，也不等于预测优势。"
        return title, intent, goal
    if angle_type == "multistage_order":
        return (
            f"{primary_keyword}：{stage_count}层为什么按{chain}这个顺序，逐层各排除多少",
            f"复算{stage_count}层筛选的固定顺序、每层before/after/excluded，并说明完成最后一层后为什么停止",
            f"逐层解释{chain}的固定顺序和空间变化，完成最后一层后明确停止。",
        )
    if angle_type == "sample_provenance":
        first = sample_stages[0]
        lookback = (first.get("params") or {}).get("lookback") or 12
        return (
            f"{primary_keyword}：近{lookback}期演示数据怎样生成数字池，为什么不能当成预测",
            f"只用演示样本复算{_stage_label(first)}的数字池和空间变化，并区分样本计算、玩法规则与预测结论",
            "追踪样本型阶段的数据来源：只证明演示样本上的确定性计算，不包装成未来预测。",
        )
    raise ValueError(f"unsupported article angle: {angle_type}")


def _angle_outline(blueprint: dict, angle_type: str) -> list[str]:
    stages = _stages(blueprint)
    chain = "→".join(_stage_label(stage) for stage in stages)
    common_end = ["边界与误区：不把统计筛选包装成预测优势", "停止条件：完成合同后不临时加新过滤器"]
    if angle_type == "mechanics_case":
        return ["玩法与计算范围", f"方法机制：{chain}", "完整可复算案例", "逐步核对候选空间", *common_end]
    if angle_type == "space_math":
        return ["先定义候选空间", "逐层计算保留与排除数量", "核对起点、终点和总排除", "为什么这些数字不是命中率", *common_end]
    if angle_type == "execution_checklist":
        return ["执行前检查参数", "实际操作步骤清单", "每一步如何核对结果", "何时必须停止", *common_end]
    if angle_type == "parameter_boundary":
        return ["哪些参数归系统研究", "哪些结果由演示样本计算", "来源能支持什么、不能支持什么", "为什么不能事后改参数", *common_end]
    if angle_type == "multistage_order":
        return ["先列出全部合同阶段", "按固定顺序逐层复算", "逐层核对before/after/excluded", "完成最后一层后停止", *common_end]
    if angle_type == "sample_provenance":
        return ["演示数据标签与样本窗口", "样本型数字池怎样确定性生成", "样本结果与玩法规则的证据边界", "为什么样本结果不是预测", *common_end]
    raise ValueError(f"unsupported article angle: {angle_type}")


def build_article_angle_contract(blueprint: dict, angle_type: str) -> dict:
    if angle_type not in allowed_angle_types(blueprint):
        raise ValueError(f"angle {angle_type} is not supported by this production contract")
    stages = _stages(blueprint)
    start, final, excluded, stage_count = _pipeline_counts(blueprint)
    primary_keyword = angle_primary_keyword(blueprint, angle_type)
    title, search_intent, summary_goal = _angle_identity_text(blueprint, angle_type, primary_keyword)
    sample_labels = [_stage_label(stage) for stage in stages if _is_sample_stage(stage)]
    static_labels = [_stage_label(stage) for stage in stages if not _is_sample_stage(stage)]
    stage_labels = [_stage_label(stage) for stage in stages]
    contract_seed = "|".join([
        str(blueprint.get("fingerprint") or blueprint.get("article_id") or ""),
        angle_type,
        _pipeline_signature(blueprint),
        ANGLE_CONTRACT_VERSION,
    ])
    return {
        "version": ANGLE_CONTRACT_VERSION,
        "contract_id": "AAC-" + hashlib.sha256(contract_seed.encode("utf-8")).hexdigest()[:16],
        "angle_type": angle_type,
        "primary_keyword": primary_keyword,
        "title": title,
        "search_intent": search_intent,
        "summary_goal": summary_goal,
        "reader_question": search_intent,
        "required_deliverable": summary_goal,
        "required_machine_facts": {
            "starting_space": start,
            "final_space": final,
            "excluded_space": excluded,
            "stage_count": stage_count,
            "stage_labels": stage_labels,
            "sample_stage_labels": sample_labels,
            "static_stage_labels": static_labels,
            "evidence_mode": _evidence_mode(blueprint),
        },
        "parameter_owner": "system_research",
        "source_parameter_attribution_allowed": False,
        "predictive_advantage_claimed": False,
        "stop_after_final_stage": True,
        "pipeline_signature": _pipeline_signature(blueprint),
        "required_outline": _angle_outline(blueprint, angle_type),
    }


def _variant_fingerprint(base: dict, contract: dict) -> str:
    raw = "|".join([
        str(base.get("fingerprint") or ""),
        str(contract.get("contract_id") or ""),
        str(contract.get("angle_type") or ""),
    ])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _variant_angle_signature(base: dict, angle_type: str) -> str:
    if angle_type == "mechanics_case":
        return str(base.get("angle_signature") or "")
    raw = f"{base.get('angle_signature') or base.get('fingerprint') or ''}|angle={angle_type}|{ANGLE_CONTRACT_VERSION}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]


def apply_article_angle(blueprint: dict, angle_type: str) -> dict:
    variant = copy.deepcopy(blueprint)
    contract = build_article_angle_contract(variant, angle_type)
    if angle_type != "mechanics_case":
        fp = _variant_fingerprint(variant, contract)
        variant["fingerprint"] = fp
        variant["article_id"] = "LCM-ANGLE-" + fp[:16]
        variant["blueprint_id"] = "BP-" + fp[:16]
        variant["slug_seed"] = f"{variant.get('slug_seed') or variant['article_id']}-{angle_type}"
    variant["angle_signature"] = _variant_angle_signature(variant, angle_type)
    variant["primary_keyword"] = contract["primary_keyword"]
    variant["title"] = contract["title"]
    variant["search_intent"] = contract["search_intent"]
    variant["summary_goal"] = contract["summary_goal"]
    variant["outline"] = list(contract["required_outline"])
    variant["information_gain_type"] = angle_type
    variant["article_angle_contract_version"] = ANGLE_CONTRACT_VERSION
    variant["angle_contract_verified"] = True
    variant["article_angle_contract"] = contract
    variant["case_structure"] = (
        str(variant.get("case_structure") or "")
        + f";angle={angle_type};pipeline={contract['pipeline_signature']}"
        + f";start={contract['required_machine_facts']['starting_space']}"
        + f";final={contract['required_machine_facts']['final_space']}"
        + f";excluded={contract['required_machine_facts']['excluded_space']}"
    )
    secondary = [str(x) for x in variant.get("secondary_keywords", []) if str(x)]
    variant["secondary_keywords"] = list(dict.fromkeys([contract["primary_keyword"], *secondary]))
    return variant


def expand_article_angle_variants(blueprint: dict) -> list[dict]:
    return [apply_article_angle(blueprint, angle_type) for angle_type in allowed_angle_types(blueprint)]


def audited_angle_type(record: dict) -> str | None:
    if str(record.get("article_angle_contract_version") or "") != ANGLE_CONTRACT_VERSION:
        return None
    if record.get("angle_contract_verified") is not True:
        return None
    angle_type = str(record.get("information_gain_type") or "")
    if angle_type not in ANGLE_TYPES:
        return None
    status = str(record.get("status") or "")
    if status in _ACTIVE_FORMAL_STATUSES and record.get("angle_approval_passed") is not True:
        return None
    return angle_type


def same_audited_angle(a: dict, b: dict) -> bool | None:
    left = audited_angle_type(a)
    right = audited_angle_type(b)
    if left is None or right is None:
        return None
    return left == right


def angle_contract_machine_values(contract: dict) -> dict:
    facts = dict(contract.get("required_machine_facts") or {})
    return {
        "starting_space": int(facts.get("starting_space") or 0),
        "final_space": int(facts.get("final_space") or 0),
        "excluded_space": int(facts.get("excluded_space") or 0),
        "stage_count": int(facts.get("stage_count") or 0),
        "stage_labels": [str(x) for x in facts.get("stage_labels", [])],
        "sample_stage_labels": [str(x) for x in facts.get("sample_stage_labels", [])],
        "static_stage_labels": [str(x) for x in facts.get("static_stage_labels", [])],
        "evidence_mode": str(facts.get("evidence_mode") or ""),
    }
