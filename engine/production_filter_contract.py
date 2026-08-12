from __future__ import annotations

from functools import lru_cache
from itertools import combinations, product

from .analysis_metrics import POSITION_INDEX


class ProductionFilterContractError(ValueError):
    pass


STATIC_ATOMS = {
    "sum_range",
    "span_range",
    "odd_even_filter",
    "big_small_filter",
    "repeat_number",
    "neighbor_number",
}
SAMPLE_ATOMS = {"cold_hot_split", "frequency_window", "omission_threshold"}
SUPPORTED_PRIMARY_ATOMS = STATIC_ATOMS | SAMPLE_ATOMS


def _play_width(play: str) -> int | None:
    value = str(play or "")
    if value in {"定位胆", "一星直选"}:
        return 1
    for marker, width in (
        ("前二", 2), ("后二", 2),
        ("前三", 3), ("中三", 3), ("后三", 3),
        ("前四", 4), ("后四", 4), ("五星", 5),
    ):
        if marker in value:
            return width
    return None


def _domain_key(play: str) -> str:
    value = str(play or "")
    width = _play_width(value)
    if "大小单双" in value:
        raise ProductionFilterContractError("大小单双 play uses categorical betting semantics; numeric primary-filter contract not enabled")
    if "组选3" in value:
        return "group3_3digit"
    if "组选6" in value:
        return "group6_3digit"
    if "组选" in value:
        if width == 2:
            return "unordered_2digit"
        raise ProductionFilterContractError(f"unsupported group play for production filter contract: {value}")
    if width is None:
        raise ProductionFilterContractError(f"cannot resolve candidate-space width for play: {value}")
    return f"ordered_{width}digit"


@lru_cache(maxsize=None)
def _domain(domain_key: str) -> tuple[tuple[int, ...], ...]:
    if domain_key.startswith("ordered_") and domain_key.endswith("digit"):
        width = int(domain_key.removeprefix("ordered_").removesuffix("digit"))
        return tuple(product(range(10), repeat=width))
    if domain_key == "unordered_2digit":
        return tuple(combinations(range(10), 2))
    if domain_key == "group6_3digit":
        return tuple(combinations(range(10), 3))
    if domain_key == "group3_3digit":
        rows = {
            tuple(sorted((repeat_digit, repeat_digit, other_digit)))
            for repeat_digit in range(10)
            for other_digit in range(10)
            if other_digit != repeat_digit
        }
        return tuple(sorted(rows))
    raise ProductionFilterContractError(f"unsupported candidate domain: {domain_key}")


def _has_neighbor(candidate: tuple[int, ...]) -> bool:
    values = sorted(set(candidate))
    return any(b - a == 1 for index, a in enumerate(values) for b in values[index + 1 :])


def _static_filter(atom: str, candidate: tuple[int, ...], width: int) -> tuple[bool, dict, str]:
    if atom == "sum_range":
        lo, hi = 3 * width, 6 * width
        return lo <= sum(candidate) <= hi, {"min": lo, "max": hi}, "digit_sum"
    if atom == "span_range":
        if width < 2:
            return False, {"min": 2, "max": 6}, "span"
        span = max(candidate) - min(candidate)
        return 2 <= span <= 6, {"min": 2, "max": 6}, "span"
    if atom == "odd_even_filter":
        odd_count = 1 if width <= 3 else 2
        return sum(value % 2 for value in candidate) == odd_count, {"odd_count": odd_count}, "odd_count"
    if atom == "big_small_filter":
        big_count = 1 if width <= 3 else 2
        return sum(value >= 5 for value in candidate) == big_count, {"big_count": big_count}, "big_count"
    if atom == "repeat_number":
        return len(set(candidate)) < len(candidate), {"has_repeat": True}, "repeat_structure"
    if atom == "neighbor_number":
        return _has_neighbor(candidate), {"pair_difference": 1, "circular_0_9": False}, "neighbor_pair"
    raise ProductionFilterContractError(f"unsupported static primary atom: {atom}")


def _frequency_pool(case_bundle: dict) -> tuple[list[int], dict]:
    freq = case_bundle.get("frequency")
    if not isinstance(freq, dict):
        raise ProductionFilterContractError("frequency case bundle missing")
    digits = freq.get("top_frequency_digits")
    if not isinstance(digits, list) or not digits:
        raise ProductionFilterContractError("top_frequency_digits missing from frequency case")
    clean = sorted({int(value) for value in digits})
    if not clean or any(value < 0 or value > 9 for value in clean):
        raise ProductionFilterContractError("invalid top_frequency_digits")
    return clean, {
        "lookback": int(freq.get("sample_size") or 12),
        "top_n": len(clean),
        "digits": clean,
    }


def _omission_pool(case_bundle: dict) -> tuple[list[int], dict]:
    omission = case_bundle.get("omission")
    if not isinstance(omission, dict):
        raise ProductionFilterContractError("omission case bundle missing")
    digits = omission.get("candidates_meeting_threshold")
    if not isinstance(digits, list) or not digits:
        raise ProductionFilterContractError("omission threshold produced no candidate digits")
    clean = sorted({int(value) for value in digits})
    return clean, {
        "lookback": int(omission.get("sample_size") or 12),
        "threshold": int(omission.get("threshold") or 0),
        "digits": clean,
    }


def _candidate_pool_filter(candidate: tuple[int, ...], digits: list[int]) -> bool:
    allowed = set(digits)
    return all(value in allowed for value in candidate)


def _build_for_atom(blueprint: dict, case_bundle: dict, atom: str) -> dict:
    play = str(blueprint.get("subject_play") or blueprint.get("play") or "")
    selector = str(blueprint.get("resolved_selector") or case_bundle.get("selector") or "")
    domain_key = _domain_key(play)
    candidates = _domain(domain_key)
    if not candidates:
        raise ProductionFilterContractError("empty starting candidate domain")
    width = len(candidates[0])

    params: dict
    metric: str
    basis: str
    support_mode: str
    if atom in STATIC_ATOMS:
        filtered = []
        params = {}
        metric = ""
        for candidate in candidates:
            matched, candidate_params, candidate_metric = _static_filter(atom, candidate, width)
            params = candidate_params
            metric = candidate_metric
            if matched:
                filtered.append(candidate)
        basis = "system_research_preset_not_source_claim"
        support_mode = "verified_rule_calculation"
    elif atom in {"cold_hot_split", "frequency_window"}:
        digits, params = _frequency_pool(case_bundle)
        filtered = [candidate for candidate in candidates if _candidate_pool_filter(candidate, digits)]
        metric = "top_frequency_digit_pool"
        basis = "synthetic_case_fixed_window_research_preset"
        support_mode = "synthetic_case_calculation"
    elif atom == "omission_threshold":
        if selector not in POSITION_INDEX or width != 1:
            raise ProductionFilterContractError("omission primary filter requires one fixed position")
        digits, params = _omission_pool(case_bundle)
        filtered = [candidate for candidate in candidates if _candidate_pool_filter(candidate, digits)]
        metric = "current_omission_threshold_digit_pool"
        basis = "synthetic_case_fixed_threshold_research_preset"
        support_mode = "synthetic_case_calculation"
    else:
        raise ProductionFilterContractError(f"unsupported primary filter atom: {atom}")

    starting = len(candidates)
    after = len(filtered)
    if after <= 0 or after >= starting:
        raise ProductionFilterContractError(
            f"primary filter must strictly reduce a non-empty candidate space: {atom} {starting}->{after}"
        )

    return {
        "contract_version": "1.0",
        "atom": atom,
        "selector": selector,
        "subject_play": play,
        "candidate_space_type": domain_key,
        "candidate_width": width,
        "metric": metric,
        "params": params,
        "basis": basis,
        "support_mode": support_mode,
        "support_refs": list(blueprint.get("rule_refs") or []),
        "starting_space": starting,
        "after_filter_space": after,
        "excluded_space": starting - after,
        "stop_after_primary_filter": True,
        "parameter_freeze_before_observation": True,
        "predictive_advantage_claimed": False,
        "source_recommendation_claimed": False,
        "method_note": (
            "该参数由系统在正文生成前冻结，只用于演示可复算筛选机制；"
            "候选空间收缩不代表命中率、收益或未来预测优势。"
        ),
    }


def build_primary_filter_spec(blueprint: dict, case_bundle: dict) -> dict:
    """Build the first valid machine-verifiable primary filter for a production article.

    The source family may contain several technique atoms. We preserve its order,
    skip position context, and choose the first supported atom whose frozen
    contract produces a strict non-empty reduction. This is a system-authored
    research preset, never a claim that the source recommended the parameter.
    """
    atoms = [
        str(atom) for atom in (blueprint.get("technique_atoms") or [])
        if str(atom) and str(atom) != "position_filter"
    ]
    errors: list[str] = []
    for atom in atoms:
        if atom not in SUPPORTED_PRIMARY_ATOMS:
            continue
        try:
            return _build_for_atom(blueprint, case_bundle, atom)
        except ProductionFilterContractError as exc:
            errors.append(f"{atom}: {exc}")
    detail = "; ".join(errors[:5]) if errors else "no supported executable atom"
    raise ProductionFilterContractError(
        f"no valid production primary-filter contract for {blueprint.get('article_id')}: {detail}"
    )
