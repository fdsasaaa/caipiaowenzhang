from __future__ import annotations

from copy import deepcopy

from .filter_pipeline import FilterPipelineError, evaluate_filter_pipeline


class RealKnowledgePipelineError(ValueError):
    pass


# Only atoms whose parameters can be frozen without looking at a sample are
# allowed into this adapter. Position is context, not a filter stage.
CONTEXT_ATOMS = {"position_filter"}
EXECUTABLE_ATOM_ORDER = (
    "sum_range",
    "span_range",
    "big_small_filter",
    "odd_even_filter",
)

STARTING_SPACES = {
    "ordered_2digit": 100,
    "ordered_3digit": 1000,
    "unordered_2digit": 45,
}

# These are explicit research presets, not values claimed by the source family.
# They are fixed before any synthetic draw is created or inspected.
PRESETS = {
    "ordered_2digit": {
        "sum_range": ("sum_range", {"min": 5, "max": 13}, "和值5–13"),
        "span_range": ("span_range", {"min": 2, "max": 7}, "跨度2–7"),
        "big_small_filter": ("big_count", {"count": 1}, "一大一小"),
        "odd_even_filter": ("odd_count", {"count": 1}, "一单一双"),
    },
    "ordered_3digit": {
        "sum_range": ("sum_range", {"min": 8, "max": 19}, "和值8–19"),
        "span_range": ("span_range", {"min": 3, "max": 7}, "跨度3–7"),
        "big_small_filter": ("big_count", {"count": 1}, "恰好1个大号"),
        "odd_even_filter": ("odd_count", {"count": 1}, "恰好1个单号"),
    },
    "unordered_2digit": {
        "sum_range": ("pair_sum_range", {"min": 5, "max": 13}, "对子和值5–13"),
        "span_range": ("span_range", {"min": 2, "max": 7}, "对子跨度2–7"),
        "big_small_filter": ("big_count", {"count": 1}, "一大一小"),
        "odd_even_filter": ("mixed_parity", {}, "一单一双"),
    },
}


def space_type_for_play(play: str) -> str:
    play = str(play or "")
    if play in {"后二大小单双", "大小单双", "猜大小", "猜单双"}:
        return "ordered_2digit"
    if "直选" in play and any(window in play for window in ("前二", "后二")):
        return "ordered_2digit"
    if "直选" in play and any(window in play for window in ("前三", "中三", "后三")):
        return "ordered_3digit"
    if "组选" in play and any(window in play for window in ("前二", "后二")):
        return "unordered_2digit"
    raise RealKnowledgePipelineError(f"play has no supported deterministic candidate space: {play!r}")


def _source_refs(record: dict) -> list[str]:
    refs = [str(x) for x in (record.get("source_refs") or []) if str(x)]
    if not refs:
        raise RealKnowledgePipelineError("real-knowledge pipeline requires source_refs")
    return refs


def _stage_atoms(record: dict) -> list[str]:
    atoms = [str(x) for x in (record.get("technique_atoms") or []) if str(x)]
    if not atoms:
        raise RealKnowledgePipelineError("real-knowledge pipeline requires technique_atoms")

    allowed = set(EXECUTABLE_ATOM_ORDER) | CONTEXT_ATOMS
    unsupported = [atom for atom in atoms if atom not in allowed]
    if unsupported:
        raise RealKnowledgePipelineError(
            "family contains atoms that cannot be converted without sample-dependent or invented parameters: "
            + ", ".join(unsupported)
        )

    selected = [atom for atom in EXECUTABLE_ATOM_ORDER if atom in atoms]
    if len(selected) < 2:
        raise RealKnowledgePipelineError("real-knowledge multistage pipeline requires at least two executable atoms")
    if len(selected) > 3:
        raise RealKnowledgePipelineError("real-knowledge validation currently permits only two or three filter stages")
    return selected


def build_real_knowledge_filter_pipeline(record: dict) -> dict:
    """Build a fail-closed, pre-frozen 2–3 stage pipeline from one real family record.

    Source provenance supports *which technique atoms* belong to the family. The
    numeric thresholds/counts below are system research presets and are never
    represented as source claims or predictive advantages.
    """
    family = str(record.get("technique_family") or record.get("family_id") or "")
    if not family:
        raise RealKnowledgePipelineError("real-knowledge pipeline requires technique_family/family_id")

    # Validate provenance and atom executability before selecting a candidate
    # space so sample-dependent families fail with the most actionable reason.
    refs = _source_refs(record)
    stage_atoms = _stage_atoms(record)
    play = str(record.get("play") or record.get("subject_play") or "")
    space_type = space_type_for_play(play)
    presets = PRESETS[space_type]

    stages = []
    for index, atom in enumerate(stage_atoms, start=1):
        op, params, label = presets[atom]
        stages.append({
            "id": f"source-stage-{index}",
            "label": label,
            "atom": atom,
            "op": op,
            "params": deepcopy(params),
            "basis": "source_family_atom_plus_prefrozen_experimental_parameter",
            "support_ref": refs[0],
            "parameter_provenance": "system_research_preset_not_source_claim",
        })

    spec = {
        "space_type": space_type,
        "starting_space": STARTING_SPACES[space_type],
        "stages": stages,
        "knowledge_family": family,
        "source_refs": refs,
        "source_support_count": int(record.get("source_support_count") or record.get("source_count") or 0),
        "source_risk_rate": float(record.get("source_risk_rate") or record.get("risk_rate") or 0.0),
        "parameter_policy": "prefrozen_research_presets_v1_not_source_claim_not_predictive",
    }

    try:
        result = evaluate_filter_pipeline(spec)
    except FilterPipelineError as exc:
        raise RealKnowledgePipelineError(str(exc)) from exc
    if result["stage_count"] not in {2, 3}:
        raise RealKnowledgePipelineError("real-knowledge pipeline must evaluate to two or three stages")
    return spec


def real_knowledge_pipeline_evidence(record: dict) -> dict:
    spec = build_real_knowledge_filter_pipeline(record)
    return {
        "filter_pipeline_spec": spec,
        "filter_pipeline_result": evaluate_filter_pipeline(spec),
        "source_parameter_boundary": (
            "source_refs support the technique-family atoms only; all numeric filter parameters are "
            "pre-frozen system research presets, not source claims and not evidence of predictive advantage"
        ),
        "registry_write": False,
        "website_write": False,
        "scheduled": False,
        "published": False,
    }
