from __future__ import annotations

import re
from dataclasses import dataclass, field

from .article_angles import ANGLE_CONTRACT_VERSION, ANGLE_TYPES, angle_contract_machine_values

_TAG_RE = re.compile(r"<[^>]+>")


@dataclass
class ArticleAngleQualityReport:
    passed: bool
    score: int
    contracted: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _plain_html(value: object) -> str:
    return re.sub(r"\s+", " ", _TAG_RE.sub(" ", str(value or ""))).strip()


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def _ordered_markers(text: str, markers: list[str]) -> bool:
    position = -1
    for marker in markers:
        found = text.find(marker, position + 1)
        if found < 0:
            return False
        position = found
    return True


def _delivery_values(delivery: dict) -> dict:
    return {
        "starting_space": delivery.get("starting_space"),
        "final_space": delivery.get("final_space"),
        "excluded_space": delivery.get("excluded_space"),
        "stage_count": delivery.get("stage_count"),
        "stage_labels": list(delivery.get("stage_labels") or []),
        "sample_stage_labels": list(delivery.get("sample_stage_labels") or []),
        "static_stage_labels": list(delivery.get("static_stage_labels") or []),
        "evidence_mode": str(delivery.get("evidence_mode") or ""),
    }


def evaluate_article_angle(packet: dict, article: dict) -> ArticleAngleQualityReport:
    contract = packet.get("article_angle_contract")
    if not isinstance(contract, dict) or not contract:
        return ArticleAngleQualityReport(passed=True, score=100, contracted=False)

    errors: list[str] = []
    warnings: list[str] = []
    if str(contract.get("version") or "") != ANGLE_CONTRACT_VERSION:
        return ArticleAngleQualityReport(
            passed=False,
            score=0,
            contracted=True,
            errors=["unsupported article_angle_contract version"],
        )

    angle_type = str(contract.get("angle_type") or "")
    if angle_type not in ANGLE_TYPES:
        errors.append("article_angle_contract has unsupported angle_type")

    if article.get("article_angle_contract_version") != ANGLE_CONTRACT_VERSION:
        errors.append("article_angle_contract_version differs from packet")
    if article.get("information_gain_type") != angle_type:
        errors.append("information_gain_type differs from article angle contract")

    delivery = article.get("angle_delivery")
    if not isinstance(delivery, dict):
        return ArticleAngleQualityReport(
            passed=False,
            score=35,
            contracted=True,
            errors=[*errors, "contracted article requires angle_delivery object"],
        )

    expected = angle_contract_machine_values(contract)
    actual = _delivery_values(delivery)
    if delivery.get("angle_type") != angle_type:
        errors.append("angle_delivery.angle_type differs from contract")
    if delivery.get("reader_question") != contract.get("reader_question"):
        errors.append("angle_delivery.reader_question differs from contract")
    for field in (
        "starting_space", "final_space", "excluded_space", "stage_count",
        "stage_labels", "sample_stage_labels", "static_stage_labels", "evidence_mode",
    ):
        if actual[field] != expected[field]:
            errors.append(f"angle_delivery.{field} differs from machine contract")

    if delivery.get("parameter_owner") != "system_research":
        errors.append("angle_delivery.parameter_owner must be system_research")
    if delivery.get("source_parameter_attribution_allowed") is not False:
        errors.append("angle_delivery must forbid source attribution of production parameters")
    if delivery.get("predictive_advantage_claimed") is not False:
        errors.append("angle_delivery must not claim predictive advantage")
    if delivery.get("stop_after_final_stage") is not True:
        errors.append("angle_delivery must stop after the final contracted stage")
    if not str(delivery.get("deliverable_summary") or "").strip():
        errors.append("angle_delivery.deliverable_summary is required")

    content = _plain_html(article.get("content"))
    guidance = article.get("practical_guidance") or {}
    start = str(expected["starting_space"])
    final = str(expected["final_space"])
    excluded = str(expected["excluded_space"])
    labels = expected["stage_labels"]
    sample_labels = expected["sample_stage_labels"]

    if angle_type == "mechanics_case":
        if "案例" not in content:
            errors.append("mechanics_case content must visibly deliver a complete example")
        if start not in content or final not in content:
            errors.append("mechanics_case must show the machine start and final candidate spaces")
        for label in labels:
            if label and label not in content:
                errors.append(f"mechanics_case content omits contracted stage label: {label}")

    elif angle_type == "space_math":
        for value, name in ((start, "starting_space"), (final, "final_space"), (excluded, "excluded_space")):
            if value not in content:
                errors.append(f"space_math content omits {name}")
        if "候选" not in content:
            errors.append("space_math content must explain the candidate space")
        if not _contains_any(content, ("排除", "筛掉", "剔除")):
            errors.append("space_math content must explain the excluded candidate count")
        if not _contains_any(content, ("计算", "复算", "注数")):
            errors.append("space_math content must visibly explain the calculation")

    elif angle_type == "execution_checklist":
        steps = guidance.get("steps") if isinstance(guidance, dict) else None
        joined = " ".join(str(x) for x in steps or [])
        if not isinstance(steps, list) or len([x for x in steps if str(x).strip()]) < max(4, expected["stage_count"]):
            errors.append("execution_checklist requires a concrete ordered step list")
        for label in labels:
            if label and label not in joined:
                errors.append(f"execution_checklist steps omit contracted stage: {label}")
        if not _contains_any(content, ("操作步骤", "实际怎么操作", "按步骤", "检查清单", "执行清单")):
            errors.append("execution_checklist content lacks a visible operation/checklist section")

    elif angle_type == "parameter_boundary":
        if "参数" not in content:
            errors.append("parameter_boundary content must explicitly discuss parameters")
        if "来源" not in content:
            errors.append("parameter_boundary content must explicitly discuss source-attribution boundaries")
        if not _contains_any(content, ("系统研究", "系统预设", "预先固定", "先固定", "冻结")):
            errors.append("parameter_boundary must identify system-owned/frozen parameter choices")
        if sample_labels and not ("演示" in content and "样本" in content):
            errors.append("parameter_boundary with sample stages must distinguish sample-derived outputs")
        if not _contains_any(content, ("不是来源推荐", "不能写成来源推荐", "不得写成来源推荐", "不等于来源推荐", "不是原文参数", "不能归因给来源")):
            errors.append("parameter_boundary must explicitly deny source ownership of production parameters")

    elif angle_type == "multistage_order":
        if expected["stage_count"] < 2:
            errors.append("multistage_order requires at least two contracted stages")
        if not _ordered_markers(content, labels):
            errors.append("multistage_order content must present all contracted stage labels in order")
        for value, name in ((start, "starting_space"), (final, "final_space"), (excluded, "excluded_space")):
            if value not in content:
                errors.append(f"multistage_order content omits {name}")
        if not _contains_any(content, ("第1层", "第一层", "第一步", "第1步")):
            warnings.append("multistage_order should visibly number the first contracted stage")

    elif angle_type == "sample_provenance":
        if not sample_labels:
            errors.append("sample_provenance requires at least one sample-derived stage")
        for label in sample_labels:
            if label and label not in content:
                errors.append(f"sample_provenance content omits sample-derived stage: {label}")
        if "演示数据，不是真实开奖记录" not in content:
            errors.append("sample_provenance must retain the standard synthetic-case label")
        if not _contains_any(content, ("不代表预测", "不能证明预测", "不用于预测", "不等于预测", "不能当成预测", "不证明未来")):
            errors.append("sample_provenance must explicitly separate sample calculation from prediction")

    score = max(0, 100 - 12 * len(dict.fromkeys(errors)) - 3 * len(dict.fromkeys(warnings)))
    errors = list(dict.fromkeys(errors))
    warnings = list(dict.fromkeys(warnings))
    return ArticleAngleQualityReport(
        passed=not errors and score >= 85,
        score=score,
        contracted=True,
        errors=errors,
        warnings=warnings,
    )
