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
SUPPORTED_METHOD_ATOMS = STATIC_ATOMS | SAMPLE_ATOMS
CONTEXT_ATOMS = {"position_filter"}

# System-authored order. It is deterministic and independent of the synthetic
# draw sample. Source families support which atoms belong to the article; they
# do not claim this stage order or the numeric presets below.
STATIC_STAGE_ORDER = (
    "sum_range",
    "span_range",
    "big_small_filter",
    "odd_even_filter",
    "repeat_number",
    "neighbor_number",
)


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
        raise ProductionFilterContractError(
            "大小单双 play uses categorical betting semantics; numeric production filter contract not enabled"
        )
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


def _static_filter(atom: str, candidate: tuple[int, ...], width: int) -> tuple[bool, dict, str, str]:
    if atom == "sum_range":
        lo, hi = 3 * width, 6 * width
        return lo <= sum(candidate) <= hi, {"min": lo, "max": hi}, "digit_sum", f"和值{lo}–{hi}"
    if atom == "span_range":
        if width < 2:
            return False, {"min": 2, "max": 6}, "span", "跨度2–6"
        span = max(candidate) - min(candidate)
        return 2 <= span <= 6, {"min": 2, "max": 6}, "span", "跨度2–6"
    if atom == "odd_even_filter":
        odd_count = 1 if width <= 3 else 2
        return (
            sum(value % 2 for value in candidate) == odd_count,
            {"odd_count": odd_count},
            "odd_count",
            f"恰好{odd_count}个单号",
        )
    if atom == "big_small_filter":
        big_count = 1 if width <= 3 else 2
        return (
            sum(value >= 5 for value in candidate) == big_count,
            {"big_count": big_count},
            "big_count",
            f"恰好{big_count}个大号",
        )
    if atom == "repeat_number":
        return (
            len(set(candidate)) < len(candidate),
            {"has_repeat": True},
            "repeat_structure",
            "至少存在一个重号",
        )
    if atom == "neighbor_number":
        return (
            _has_neighbor(candidate),
            {"pair_difference": 1, "circular_0_9": False},
            "neighbor_pair",
            "至少存在一对差1邻号",
        )
    raise ProductionFilterContractError(f"unsupported static production atom: {atom}")


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
    if any(value < 0 or value > 9 for value in clean):
        raise ProductionFilterContractError("invalid omission candidate digits")
    return clean, {
        "lookback": int(omission.get("sample_size") or 12),
        "threshold": int(omission.get("threshold") or 0),
        "digits": clean,
    }


def _candidate_pool_filter(candidate: tuple[int, ...], digits: list[int]) -> bool:
    allowed = set(digits)
    return all(value in allowed for value in candidate)


def _method_atoms(blueprint: dict) -> list[str]:
    atoms = [
        str(atom) for atom in (blueprint.get("technique_atoms") or [])
        if str(atom) and str(atom) not in CONTEXT_ATOMS
    ]
    if not atoms:
        raise ProductionFilterContractError("production article has no method atom after context removal")
    unsupported = sorted({atom for atom in atoms if atom not in SUPPORTED_METHOD_ATOMS})
    if unsupported:
        raise ProductionFilterContractError(
            "production article contains unsupported method atoms: " + ", ".join(unsupported)
        )
    return list(dict.fromkeys(atoms))


def _stage_groups(atoms: list[str]) -> list[tuple[str, ...]]:
    atom_set = set(atoms)
    groups: list[tuple[str, ...]] = []
    for atom in STATIC_STAGE_ORDER:
        if atom in atom_set:
            groups.append((atom,))

    # frequency_window is a required window definition, not a second independent
    # filter when the same family also says cold_hot_split. Represent the pair as
    # one compound, auditable frequency-pool stage instead of a duplicate no-op.
    frequency_atoms = tuple(
        atom for atom in ("cold_hot_split", "frequency_window") if atom in atom_set
    )
    if frequency_atoms:
        groups.append(frequency_atoms)
    if "omission_threshold" in atom_set:
        groups.append(("omission_threshold",))
    return groups


def _static_stage(
    atom: str,
    candidates: list[tuple[int, ...]],
    width: int,
) -> tuple[list[tuple[int, ...]], dict]:
    filtered: list[tuple[int, ...]] = []
    params: dict = {}
    metric = ""
    label = atom
    for candidate in candidates:
        matched, candidate_params, candidate_metric, candidate_label = _static_filter(atom, candidate, width)
        params = candidate_params
        metric = candidate_metric
        label = candidate_label
        if matched:
            filtered.append(candidate)
    return filtered, {
        "atom": atom,
        "covered_atoms": [atom],
        "op": atom,
        "metric": metric,
        "params": params,
        "label": label,
        "basis": "experimental_parameter",
        "support_mode": "verified_rule_calculation",
        "selection_rule_freeze_before_observation": True,
        "resolved_parameters_derived_from_synthetic_case": False,
        "parameter_freeze_before_observation": True,
        "parameter_provenance": "system_research_preset_not_source_claim",
    }


def _frequency_stage(
    covered_atoms: tuple[str, ...],
    candidates: list[tuple[int, ...]],
    case_bundle: dict,
) -> tuple[list[tuple[int, ...]], dict]:
    digits, params = _frequency_pool(case_bundle)
    filtered = [candidate for candidate in candidates if _candidate_pool_filter(candidate, digits)]
    if len(covered_atoms) == 2:
        label = f"近{params['lookback']}期冷热/频率前{params['top_n']}数字池"
        atom = "cold_hot_frequency_window"
    elif covered_atoms[0] == "cold_hot_split":
        label = f"近{params['lookback']}期热号前{params['top_n']}数字池"
        atom = "cold_hot_split"
    else:
        label = f"近{params['lookback']}期频率前{params['top_n']}数字池"
        atom = "frequency_window"
    return filtered, {
        "atom": atom,
        "covered_atoms": list(covered_atoms),
        "op": "digit_pool",
        "metric": "top_frequency_digit_pool",
        "params": params,
        "label": label,
        "basis": "synthetic_case_fixed_rule",
        "support_mode": "synthetic_case_calculation",
        "selection_rule": {
            "lookback": params["lookback"],
            "ranking": "frequency_desc_then_digit_asc",
            "top_n": params["top_n"],
        },
        "selection_rule_freeze_before_observation": True,
        "resolved_parameters_derived_from_synthetic_case": True,
        "parameter_freeze_before_observation": False,
        "parameter_provenance": (
            "selection rule is system-prefrozen; resolved digit pool is calculated from deterministic synthetic case data"
        ),
    }


def _omission_stage(
    candidates: list[tuple[int, ...]],
    case_bundle: dict,
    selector: str,
    width: int,
) -> tuple[list[tuple[int, ...]], dict]:
    if selector not in POSITION_INDEX or width != 1:
        raise ProductionFilterContractError("omission filter requires one fixed position")
    digits, params = _omission_pool(case_bundle)
    filtered = [candidate for candidate in candidates if _candidate_pool_filter(candidate, digits)]
    return filtered, {
        "atom": "omission_threshold",
        "covered_atoms": ["omission_threshold"],
        "op": "digit_pool",
        "metric": "current_omission_threshold_digit_pool",
        "params": params,
        "label": f"近{params['lookback']}期当前遗漏≥{params['threshold']}数字池",
        "basis": "synthetic_case_fixed_rule",
        "support_mode": "synthetic_case_calculation",
        "selection_rule": {
            "lookback": params["lookback"],
            "threshold": params["threshold"],
            "comparison": ">=",
        },
        "selection_rule_freeze_before_observation": True,
        "resolved_parameters_derived_from_synthetic_case": True,
        "parameter_freeze_before_observation": False,
        "parameter_provenance": (
            "lookback/threshold rule is system-prefrozen; resolved digit pool is calculated from deterministic synthetic case data"
        ),
    }


def build_production_filter_contract(blueprint: dict, case_bundle: dict) -> dict:
    """Bind every reader-facing method atom to an auditable production stage.

    The source family supports broad method provenance only. Stage order, static
    presets and sample-selection rules are system research choices fixed before
    article prose generation. Exact sample-derived digit pools are *calculated*
    from deterministic synthetic case data and are never described as pre-known.

    Every stage must make a strict non-empty reduction. A method that would be a
    no-op under the frozen contract blocks the candidate instead of remaining in
    SEO/title while being silently ignored.
    """
    play = str(blueprint.get("subject_play") or blueprint.get("play") or "")
    selector = str(blueprint.get("resolved_selector") or case_bundle.get("selector") or "")
    domain_key = _domain_key(play)
    original = list(_domain(domain_key))
    if not original:
        raise ProductionFilterContractError("empty starting candidate domain")
    width = len(original[0])
    method_atoms = _method_atoms(blueprint)
    groups = _stage_groups(method_atoms)
    if not groups:
        raise ProductionFilterContractError("no executable production stage groups")

    current = original
    stages: list[dict] = []
    covered: list[str] = []
    for index, group in enumerate(groups, start=1):
        before = len(current)
        if len(group) == 1 and group[0] in STATIC_ATOMS:
            filtered, metadata = _static_stage(group[0], current, width)
        elif set(group).issubset({"cold_hot_split", "frequency_window"}):
            filtered, metadata = _frequency_stage(group, current, case_bundle)
        elif group == ("omission_threshold",):
            filtered, metadata = _omission_stage(current, case_bundle, selector, width)
        else:
            raise ProductionFilterContractError("unsupported production stage group: " + ",".join(group))

        after = len(filtered)
        if after <= 0:
            raise ProductionFilterContractError(
                f"stage {index} ({'+'.join(group)}) empties candidate space: {before}->0"
            )
        if after >= before:
            raise ProductionFilterContractError(
                f"stage {index} ({'+'.join(group)}) does not make a strict reduction: {before}->{after}"
            )

        stage = {
            "id": f"production-stage-{index}",
            "index": index,
            **metadata,
            "before_space": before,
            "after_space": after,
            "excluded_space": before - after,
            "support_refs": (
                ["case_bundle"]
                if metadata["support_mode"] == "synthetic_case_calculation"
                else list(blueprint.get("rule_refs") or [])
            ),
            "predictive_advantage_claimed": False,
            "source_recommendation_claimed": False,
        }
        stages.append(stage)
        covered.extend(stage["covered_atoms"])
        current = filtered

    if set(covered) != set(method_atoms):
        missing = sorted(set(method_atoms) - set(covered))
        raise ProductionFilterContractError(
            "reader-facing method atoms were not bound to executable/context stages: " + ", ".join(missing)
        )

    starting = len(original)
    final = len(current)
    result = {
        "candidate_space_type": domain_key,
        "space_type": domain_key,
        "starting_space": starting,
        "final_space": final,
        "total_excluded": starting - final,
        "stage_count": len(stages),
        "stages": stages,
    }
    spec = {
        "contract_version": "2.0",
        "space_type": domain_key,
        "starting_space": starting,
        "stages": [
            {
                key: stage[key]
                for key in (
                    "id", "index", "label", "atom", "covered_atoms", "op", "metric", "params",
                    "basis", "support_mode", "support_refs", "selection_rule_freeze_before_observation",
                    "resolved_parameters_derived_from_synthetic_case", "parameter_freeze_before_observation",
                    "parameter_provenance",
                )
                if key in stage
            }
            for stage in stages
        ],
        "method_atoms": method_atoms,
        "stage_order_owner": "system_research",
        "source_parameter_attribution": False,
        "source_parameter_boundary": (
            "source_refs support broad technique-family atoms only; stage order, static presets and sample-selection rules are system research choices"
        ),
    }

    first = stages[0]
    primary = {
        "contract_version": "2.0",
        "atom": first["atom"],
        "covered_atoms": first["covered_atoms"],
        "selector": selector,
        "subject_play": play,
        "candidate_space_type": domain_key,
        "candidate_width": width,
        "metric": first["metric"],
        "params": first["params"],
        "basis": first["basis"],
        "support_mode": first["support_mode"],
        "support_refs": first["support_refs"],
        "starting_space": starting,
        "after_filter_space": final if len(stages) > 1 else first["after_space"],
        "excluded_space": (starting - final) if len(stages) > 1 else first["excluded_space"],
        "stop_after_primary_filter": len(stages) == 1,
        "selection_rule_freeze_before_observation": first["selection_rule_freeze_before_observation"],
        "resolved_parameters_derived_from_synthetic_case": first["resolved_parameters_derived_from_synthetic_case"],
        "parameter_freeze_before_observation": first["parameter_freeze_before_observation"],
        "predictive_advantage_claimed": False,
        "source_recommendation_claimed": False,
        "method_note": (
            "production filter parameters are system-owned research choices; machine candidate-space reduction does not imply predictive advantage"
        ),
    }

    return {
        "contract_version": "2.0",
        "mode": "single_stage" if len(stages) == 1 else "multistage",
        "method_atoms": method_atoms,
        "method_atoms_covered": list(dict.fromkeys(covered)),
        "context_atoms": [
            str(atom) for atom in (blueprint.get("technique_atoms") or []) if str(atom) in CONTEXT_ATOMS
        ],
        "primary_filter_spec": primary,
        "filter_pipeline_spec": spec,
        "filter_pipeline_result": result,
        "source_parameter_attribution": False,
        "predictive_advantage_claimed": False,
    }


def build_primary_filter_spec(blueprint: dict, case_bundle: dict) -> dict:
    """Backward-compatible single-stage API.

    Multi-method articles must use build_production_filter_contract so no method
    label can be silently ignored.
    """
    contract = build_production_filter_contract(blueprint, case_bundle)
    if contract["mode"] != "single_stage":
        raise ProductionFilterContractError(
            "multiple reader-facing method atoms require the production multistage contract"
        )
    return contract["primary_filter_spec"]
