from __future__ import annotations

import hashlib

from .filter_pipeline import evaluate_filter_pipeline, final_pipeline_candidate_strings
from .knowledge_io import iter_brbcw_families


class RealKnowledgeCompositionError(ValueError):
    pass


COMPOSITION_ID = "RK-COMP-LAST3-SUM-SPAN-V1"
PLAY = "后三直选"
RULE_REF = "SSC-HIST-MECH-3STAR-LAST-V1"
SPACE_TYPE = "ordered_3digit"
STARTING_SPACE = 1000
BINDING_BASIS = "archive_position_mask_experimental_binding_not_source_play_claim"
COMPOSITION_BASIS = "system_authored_cross_family_composition_not_source_claim"
PARAMETER_POLICY = "prefrozen_research_presets_v1_not_source_claim_not_predictive"

SUM_FAMILY = {
    "family_id": "FAM-c7549b61f340ef66",
    "atom_family": ["position_filter", "sum_range"],
    "executable_atom": "sum_range",
    "source_ref": "BRBCW-006020",
    "source_support_count": 30,
    "source_risk_rate": 0.400,
    "position": "后三",
}

SPAN_FAMILY = {
    "family_id": "FAM-c93cfcc1527bf6f8",
    "atom_family": ["position_filter", "span_range"],
    "executable_atom": "span_range",
    "source_ref": "BRBCW-002590",
    "source_support_count": 29,
    "source_risk_rate": 0.379,
    "position": "后三",
}

EXPECTED_STAGE_AFTER = [760, 534]
EXPECTED_STAGE_EXCLUDED = [240, 226]
EXPECTED_FINAL_SPACE = 534
EXPECTED_TOTAL_EXCLUDED = 466
EXPECTED_CANDIDATE_SHA256 = "20e0d1759e51aea0e10d93eb3ccb71af5a2aa5ec659ca72fc8d856cb16a9fa95"


def _family(family_id: str) -> dict:
    family = next((row for row in iter_brbcw_families() if row.get("f") == family_id), None)
    if family is None:
        raise RealKnowledgeCompositionError(f"family not found in archive: {family_id}")
    return family


def _validate_source_family(expected: dict) -> dict:
    family = _family(expected["family_id"])
    if list(family.get("a") or []) != expected["atom_family"]:
        raise RealKnowledgeCompositionError(
            f"atom family changed for {expected['family_id']}: {family.get('a')!r}"
        )
    if expected["source_ref"] not in set(family.get("e") or []):
        raise RealKnowledgeCompositionError(f"source ref changed for {expected['family_id']}")
    if int(family.get("n") or 0) != expected["source_support_count"]:
        raise RealKnowledgeCompositionError(f"source support changed for {expected['family_id']}")
    if float(family.get("r") or 0.0) != expected["source_risk_rate"]:
        raise RealKnowledgeCompositionError(f"source risk changed for {expected['family_id']}")
    if expected["position"] not in set(family.get("p") or []):
        raise RealKnowledgeCompositionError(f"position mask changed for {expected['family_id']}")
    if "时时彩" not in set(family.get("l") or []):
        raise RealKnowledgeCompositionError(f"lottery mask changed for {expected['family_id']}")
    return family


def build_sum_span_composite_pipeline() -> dict:
    """Compose two independently source-backed atoms into one system-authored experiment.

    Neither archived source is allowed to support the other atom, the stage
    order, or the numeric thresholds. Those are explicit system research
    choices, frozen before any example/sample is inspected.
    """
    _validate_source_family(SUM_FAMILY)
    _validate_source_family(SPAN_FAMILY)

    return {
        "space_type": SPACE_TYPE,
        "starting_space": STARTING_SPACE,
        "composition_id": COMPOSITION_ID,
        "play": PLAY,
        "rule_ref": RULE_REF,
        "binding_basis": BINDING_BASIS,
        "composition_basis": COMPOSITION_BASIS,
        "parameter_policy": PARAMETER_POLICY,
        "source_families": [dict(SUM_FAMILY), dict(SPAN_FAMILY)],
        "stages": [
            {
                "id": "source-stage-sum",
                "label": "和值8–19",
                "atom": "sum_range",
                "op": "sum_range",
                "params": {"min": 8, "max": 19},
                "basis": "independent_source_atom_plus_prefrozen_experimental_parameter",
                "source_family": SUM_FAMILY["family_id"],
                "support_ref": SUM_FAMILY["source_ref"],
                "parameter_provenance": "system_research_preset_not_source_claim",
                "composition_order_provenance": "system_research_order_not_source_claim",
            },
            {
                "id": "source-stage-span",
                "label": "跨度3–7",
                "atom": "span_range",
                "op": "span_range",
                "params": {"min": 3, "max": 7},
                "basis": "independent_source_atom_plus_prefrozen_experimental_parameter",
                "source_family": SPAN_FAMILY["family_id"],
                "support_ref": SPAN_FAMILY["source_ref"],
                "parameter_provenance": "system_research_preset_not_source_claim",
                "composition_order_provenance": "system_research_order_not_source_claim",
            },
        ],
    }


def _candidate_sha256(candidates: list[str]) -> str:
    payload = ("\n".join(candidates) + "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_sum_span_composite_evidence() -> dict:
    spec = build_sum_span_composite_pipeline()
    result = evaluate_filter_pipeline(spec)
    candidates = final_pipeline_candidate_strings(spec)
    candidate_sha256 = _candidate_sha256(candidates)

    actual_after = [stage["after_space"] for stage in result["stages"]]
    actual_excluded = [stage["excluded_space"] for stage in result["stages"]]
    if actual_after != EXPECTED_STAGE_AFTER:
        raise RealKnowledgeCompositionError(f"stage after-spaces changed: {actual_after}")
    if actual_excluded != EXPECTED_STAGE_EXCLUDED:
        raise RealKnowledgeCompositionError(f"stage excluded-spaces changed: {actual_excluded}")
    if result["final_space"] != EXPECTED_FINAL_SPACE:
        raise RealKnowledgeCompositionError(f"final space changed: {result['final_space']}")
    if result["total_excluded"] != EXPECTED_TOTAL_EXCLUDED:
        raise RealKnowledgeCompositionError(f"total exclusion changed: {result['total_excluded']}")
    if len(candidates) != EXPECTED_FINAL_SPACE:
        raise RealKnowledgeCompositionError("final candidate enumeration length mismatch")
    if candidate_sha256 != EXPECTED_CANDIDATE_SHA256:
        raise RealKnowledgeCompositionError("final candidate enumeration hash changed")

    return {
        "status": "offline_composite_pass",
        "composition_id": COMPOSITION_ID,
        "play": PLAY,
        "rule_ref": RULE_REF,
        "binding_basis": BINDING_BASIS,
        "composition_basis": COMPOSITION_BASIS,
        "parameter_policy": PARAMETER_POLICY,
        "source_families": [dict(SUM_FAMILY), dict(SPAN_FAMILY)],
        "pipeline_spec": spec,
        "pipeline_result": result,
        "final_candidate_count": len(candidates),
        "final_candidate_sha256": candidate_sha256,
        "final_candidate_preview_first": candidates[:20],
        "final_candidate_preview_last": candidates[-20:],
        "source_boundary": (
            "BRBCW-006020 supports only the sum_range family atom; BRBCW-002590 supports only the "
            "span_range family atom. Combining the atoms, using sum before span, and choosing 8–19 / 3–7 "
            "are system-authored pre-frozen research choices, not source claims and not evidence of predictive advantage."
        ),
        "paid_model_call": False,
        "registry_write": False,
        "website_write": False,
        "scheduled": False,
        "published": False,
    }
