from __future__ import annotations

from functools import lru_cache
from itertools import product

CONTRACT_VERSION = "1.0"
PARAMETER_BASIS = "system_research_prefrozen"

CONTEXT_ATOMS = {"position_filter"}
DETERMINISTIC_PRIMARY_ATOMS = {
    "sum_range",
    "span_range",
    "odd_even_filter",
    "big_small_filter",
}
# These atoms imply filtering/selection in a practical article but are not safe
# for this single-stage production contract without additional source/sample or
# multi-stage bindings.
OTHER_FILTER_ATOMS = {
    "cold_hot_split",
    "frequency_window",
    "omission_threshold",
    "dan_candidate",
    "kill_candidate",
    "compound_selection",
    "recent_digit_exclusion",
}
FILTER_METHOD_ATOMS = DETERMINISTIC_PRIMARY_ATOMS | OTHER_FILTER_ATOMS

SELECTOR_WIDTH = {
    "万位": 1,
    "千位": 1,
    "百位": 1,
    "十位": 1,
    "个位": 1,
    "前二": 2,
    "后二": 2,
    "前三": 3,
    "中三": 3,
    "后三": 3,
    "前四": 4,
    "后四": 4,
    "五星": 5,
}

SUM_RANGE_BY_WIDTH = {
    2: {"min": 6, "max": 12},
    3: {"min": 8, "max": 19},
    4: {"min": 12, "max": 24},
    5: {"min": 16, "max": 29},
}
SPAN_RANGE_BY_WIDTH = {
    2: {"min": 2, "max": 7},
    3: {"min": 3, "max": 7},
    4: {"min": 3, "max": 8},
    5: {"min": 4, "max": 8},
}


class ProductionFilterContractError(ValueError):
    pass


def _is_ordered_direct_domain(play: str, width: int) -> bool:
    value = str(play or "")
    if value == "定位胆":
        return width == 1
    return "直选" in value and width >= 2


def _parameters(atom: str, width: int) -> tuple[str, dict] | None:
    if atom == "sum_range":
        params = SUM_RANGE_BY_WIDTH.get(width)
        return ("sum_range", dict(params)) if params else None
    if atom == "span_range":
        params = SPAN_RANGE_BY_WIDTH.get(width)
        return ("span_range", dict(params)) if params else None
    if atom == "odd_even_filter":
        return "odd_count", {"count": (width + 1) // 2}
    if atom == "big_small_filter":
        return "big_count", {"count": (width + 1) // 2}
    return None


def _matches(candidate: tuple[int, ...], op: str, params: dict) -> bool:
    if op == "sum_range":
        return int(params["min"]) <= sum(candidate) <= int(params["max"])
    if op == "span_range":
        span = max(candidate) - min(candidate)
        return int(params["min"]) <= span <= int(params["max"])
    if op == "odd_count":
        return sum(value % 2 for value in candidate) == int(params["count"])
    if op == "big_count":
        return sum(value >= 5 for value in candidate) == int(params["count"])
    raise ProductionFilterContractError(f"unsupported production filter op: {op}")


@lru_cache(maxsize=None)
def _count_after(width: int, op: str, frozen_params: tuple[tuple[str, int], ...]) -> int:
    params = dict(frozen_params)
    return sum(
        1
        for candidate in product(range(10), repeat=width)
        if _matches(candidate, op, params)
    )


def assess_primary_filter_contract(*, play: str, selector: str | None, atoms: list[str]) -> dict:
    atom_set = {str(atom) for atom in (atoms or []) if str(atom)}
    filter_atoms = sorted(atom_set & FILTER_METHOD_ATOMS)
    deterministic = sorted(atom_set & DETERMINISTIC_PRIMARY_ATOMS)

    if not filter_atoms:
        return {
            "status": "not_required",
            "reason": "no_practical_filter_atom",
            "spec": None,
        }
    if len(filter_atoms) != 1:
        return {
            "status": "blocked",
            "reason": "multiple_filter_atoms_require_multistage_contract",
            "filter_atoms": filter_atoms,
            "spec": None,
        }
    if len(deterministic) != 1:
        return {
            "status": "blocked",
            "reason": "filter_atom_requires_source_or_sample_parameter_contract",
            "filter_atoms": filter_atoms,
            "spec": None,
        }

    resolved_selector = str(selector or "")
    width = SELECTOR_WIDTH.get(resolved_selector)
    if width is None:
        return {
            "status": "blocked",
            "reason": "primary_filter_selector_width_unresolved",
            "filter_atoms": filter_atoms,
            "spec": None,
        }
    if not _is_ordered_direct_domain(play, width):
        return {
            "status": "blocked",
            "reason": "primary_filter_target_domain_not_supported",
            "filter_atoms": filter_atoms,
            "spec": None,
        }

    atom = deterministic[0]
    parameter_contract = _parameters(atom, width)
    if parameter_contract is None:
        return {
            "status": "blocked",
            "reason": "primary_filter_parameter_policy_missing",
            "filter_atoms": filter_atoms,
            "spec": None,
        }
    op, params = parameter_contract
    starting = 10 ** width
    frozen_params = tuple(sorted((str(key), int(value)) for key, value in params.items()))
    after = _count_after(width, op, frozen_params)
    if after <= 0 or after >= starting:
        raise ProductionFilterContractError(
            f"production primary filter must reduce but not empty candidate space: {starting} -> {after}"
        )

    spec = {
        "contract_version": CONTRACT_VERSION,
        "selector": resolved_selector,
        "width": width,
        "space_type": f"ordered_{width}digit_direct",
        "atom": atom,
        "op": op,
        "params": dict(params),
        "basis": PARAMETER_BASIS,
        "parameter_owner": "system_research",
        "source_parameter_attribution": False,
        "parameter_freeze_before_observation": True,
        "starting_space": starting,
        "after_filter_space": after,
        "excluded_space": starting - after,
        "support_ref": None,
        "evidence_boundary": (
            "source provenance may support the broad technique atom, but this concrete filter parameter is a system-prefrozen research choice"
        ),
    }
    return {
        "status": "ready",
        "reason": "deterministic_single_stage_filter_bound",
        "filter_atoms": filter_atoms,
        "spec": spec,
    }


def primary_filter_signature(spec: dict | None) -> str:
    if not isinstance(spec, dict) or not spec:
        return ""
    params = spec.get("params") or {}
    param_text = ",".join(f"{key}={params[key]}" for key in sorted(params))
    return "|".join([
        str(spec.get("contract_version") or ""),
        str(spec.get("selector") or ""),
        str(spec.get("atom") or ""),
        str(spec.get("op") or ""),
        param_text,
        str(spec.get("starting_space") or ""),
        str(spec.get("after_filter_space") or ""),
    ])
