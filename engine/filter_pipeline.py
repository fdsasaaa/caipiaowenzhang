from __future__ import annotations

from itertools import combinations, product


class FilterPipelineError(ValueError):
    pass


def _ordered_2digit_domain() -> list[tuple[int, int]]:
    return list(product(range(10), repeat=2))


def _ordered_3digit_domain() -> list[tuple[int, int, int]]:
    return list(product(range(10), repeat=3))


def _unordered_2digit_domain() -> list[tuple[int, int]]:
    return list(combinations(range(10), 2))


def _domain(space_type: str):
    if space_type == "ordered_2digit":
        return _ordered_2digit_domain()
    if space_type == "ordered_3digit":
        return _ordered_3digit_domain()
    if space_type == "unordered_2digit":
        return _unordered_2digit_domain()
    raise FilterPipelineError(f"unsupported space_type: {space_type}")


def _int_param(params: dict, key: str) -> int:
    value = params.get(key)
    if not isinstance(value, int):
        raise FilterPipelineError(f"{key} must be int")
    return value


def _digits_param(params: dict) -> set[int]:
    values = params.get("digits")
    if not isinstance(values, list) or not values:
        raise FilterPipelineError("digits must be a non-empty list")
    digits = set()
    for value in values:
        if not isinstance(value, int) or value < 0 or value > 9:
            raise FilterPipelineError("digits must contain integers 0..9")
        digits.add(value)
    return digits


def _matches(candidate: tuple[int, ...], op: str, params: dict) -> bool:
    if op == "sum_range":
        lo, hi = _int_param(params, "min"), _int_param(params, "max")
        return lo <= sum(candidate) <= hi
    if op == "span_range":
        lo, hi = _int_param(params, "min"), _int_param(params, "max")
        span = max(candidate) - min(candidate)
        return lo <= span <= hi
    if op == "odd_count":
        count = _int_param(params, "count")
        return sum(value % 2 for value in candidate) == count
    if op == "big_count":
        count = _int_param(params, "count")
        return sum(value >= 5 for value in candidate) == count
    if op == "distinct_count":
        count = _int_param(params, "count")
        return len(set(candidate)) == count
    if op == "digit_pool":
        digits = _digits_param(params)
        return all(value in digits for value in candidate)
    if op == "pair_sum_range":
        if len(candidate) != 2:
            raise FilterPipelineError("pair_sum_range requires a 2-digit space")
        lo, hi = _int_param(params, "min"), _int_param(params, "max")
        return lo <= sum(candidate) <= hi
    if op == "mixed_parity":
        if len(candidate) != 2:
            raise FilterPipelineError("mixed_parity requires a 2-digit space")
        return candidate[0] % 2 != candidate[1] % 2
    raise FilterPipelineError(f"unsupported filter op: {op}")


def evaluate_filter_pipeline(spec: dict) -> dict:
    if not isinstance(spec, dict) or not spec:
        raise FilterPipelineError("filter pipeline spec must be a non-empty object")
    space_type = str(spec.get("space_type") or "")
    candidates = _domain(space_type)
    expected_start = spec.get("starting_space")
    if expected_start is not None and expected_start != len(candidates):
        raise FilterPipelineError(
            f"starting_space mismatch: expected {len(candidates)} for {space_type}, got {expected_start}"
        )
    stages = spec.get("stages")
    if not isinstance(stages, list) or len(stages) < 2:
        raise FilterPipelineError("filter pipeline requires at least two stages")

    seen_ids: set[str] = set()
    results: list[dict] = []
    for index, stage in enumerate(stages, start=1):
        if not isinstance(stage, dict):
            raise FilterPipelineError(f"stage {index} must be an object")
        stage_id = str(stage.get("id") or "").strip()
        op = str(stage.get("op") or "").strip()
        if not stage_id or stage_id in seen_ids:
            raise FilterPipelineError(f"stage {index} requires unique id")
        seen_ids.add(stage_id)
        params = stage.get("params") or {}
        if not isinstance(params, dict):
            raise FilterPipelineError(f"stage {stage_id} params must be an object")
        before = len(candidates)
        filtered = [candidate for candidate in candidates if _matches(candidate, op, params)]
        after = len(filtered)
        if after >= before:
            raise FilterPipelineError(
                f"stage {stage_id} must reduce candidate space: {before} -> {after}"
            )
        results.append({
            "index": index,
            "id": stage_id,
            "label": str(stage.get("label") or stage_id),
            "atom": stage.get("atom"),
            "op": op,
            "params": dict(params),
            "basis": stage.get("basis") or "experimental_parameter",
            "support_ref": stage.get("support_ref"),
            "before_space": before,
            "after_space": after,
            "excluded_space": before - after,
        })
        candidates = filtered

    return {
        "space_type": space_type,
        "starting_space": len(_domain(space_type)),
        "final_space": len(candidates),
        "total_excluded": len(_domain(space_type)) - len(candidates),
        "stage_count": len(results),
        "stages": results,
    }
