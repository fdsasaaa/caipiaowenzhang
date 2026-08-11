from __future__ import annotations

import re
from dataclasses import dataclass, field

FILTER_ATOMS = {
    "sum_range", "span_range", "omission_threshold", "cold_hot_split", "frequency_window",
    "odd_even_filter", "big_small_filter", "dan_candidate", "kill_candidate", "compound_selection",
    "recent_digit_exclusion", "position_filter",
}


@dataclass
class EditorialQualityReport:
    passed: bool
    score: int
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _first_int(value: object) -> int | None:
    if not isinstance(value, str):
        return None
    match = re.search(r"(?<!\d)(\d{1,9})(?!\d)", value.replace(",", ""))
    return int(match.group(1)) if match else None


def evaluate_editorial(packet: dict, article: dict) -> EditorialQualityReport:
    """V2.1 reader-value gate. Legacy packets without an editorial contract pass unchanged."""
    version = packet.get("editorial_contract_version")
    if not version:
        return EditorialQualityReport(passed=True, score=100)

    score = 100
    errors: list[str] = []
    warnings: list[str] = []
    guidance = article.get("practical_guidance")
    if not isinstance(guidance, dict):
        return EditorialQualityReport(
            passed=False, score=45,
            errors=["V2.1 article requires practical_guidance object"],
        )

    required = (
        "steps", "starting_space", "after_primary_filter_space",
        "parameter_freeze_rule", "stop_condition", "next_step_policy",
    )
    for field in required:
        value = guidance.get(field)
        if value in (None, "", []):
            errors.append(f"practical_guidance missing {field}")
            score -= 12

    steps = guidance.get("steps")
    minimum = int(packet.get("practicality", {}).get("minimum_concrete_steps", 4))
    if not isinstance(steps, list) or len([x for x in steps if str(x).strip()]) < minimum:
        errors.append(f"practical_guidance requires at least {minimum} concrete steps")
        score -= 20

    content = str(article.get("content") or "")
    if not any(marker in content for marker in ("实际怎么操作", "操作步骤", "按步骤", "手工操作")):
        errors.append("article content lacks a visible practical operation section")
        score -= 15

    freeze_rule = str(guidance.get("parameter_freeze_rule") or "")
    if "固定" not in freeze_rule and "冻结" not in freeze_rule:
        errors.append("parameter_freeze_rule must explicitly freeze parameters before observation")
        score -= 10

    stop_condition = str(guidance.get("stop_condition") or "")
    if not any(term in stop_condition for term in ("停止", "停下", "不再", "不得继续", "不要继续")):
        errors.append("stop_condition must explicitly tell the reader when to stop adding filters")
        score -= 10

    next_step_policy = str(guidance.get("next_step_policy") or "")
    if not any(term in next_step_policy for term in ("已验证", "验证", "规则", "证据")):
        errors.append("next_step_policy must bind any extra filter to verified evidence/rules")
        score -= 10

    atoms = set(packet.get("immutable_facts", {}).get("technique_atoms") or [])
    if atoms.intersection(FILTER_ATOMS):
        start = str(guidance.get("starting_space") or "")
        after = str(guidance.get("after_primary_filter_space") or "")
        if start in {"不适用", "N/A", "na"} or after in {"不适用", "N/A", "na"}:
            warnings.append("filter article does not quantify candidate-space change")
            score -= 8
        else:
            start_n = _first_int(start)
            after_n = _first_int(after)
            if start_n is not None and after_n is not None:
                if after_n >= start_n:
                    errors.append("primary filter must demonstrate an actual reduction in candidate space")
                    score -= 20
                reduction = start_n - after_n
                if reduction > 0 and str(reduction) not in content:
                    warnings.append("content does not explicitly state the number of candidates removed")
                    score -= 5
            elif start == after:
                errors.append("starting_space and after_primary_filter_space must not be identical")
                score -= 15

    passed = not errors and score >= 85
    return EditorialQualityReport(
        passed=passed,
        score=max(0, score),
        errors=list(dict.fromkeys(errors)),
        warnings=list(dict.fromkeys(warnings)),
    )
