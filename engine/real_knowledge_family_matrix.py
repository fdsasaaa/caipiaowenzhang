from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .knowledge_io import iter_brbcw_families
from .real_knowledge_multistage import (
    CONTEXT_ATOMS,
    EXECUTABLE_ATOM_ORDER,
    RealKnowledgePipelineError,
    build_real_knowledge_filter_pipeline,
)
from .filter_pipeline import evaluate_filter_pipeline, final_pipeline_candidate_strings


class RealKnowledgeFamilyMatrixError(ValueError):
    pass


TARGET_ALREADY_ACCEPTED_FAMILY = "FAM-32137acbb90340b9"
ELIGIBLE_LOTTERIES = {"时时彩", "分分彩"}
MIN_SOURCE_SUPPORT = 5
MAX_SOURCE_RISK_RATE = 0.50

PLAY_BINDINGS = (
    {
        "position": "后三",
        "play": "后三直选",
        "space_type": "ordered_3digit",
        "rule_ref": "SSC-HIST-MECH-3STAR-LAST-V1",
        "source_positions": ["百位", "十位", "个位"],
    },
    {
        "position": "后二",
        "play": "后二直选",
        "space_type": "ordered_2digit",
        "rule_ref": "SSC-HIST-MECH-2STAR-LAST-V1",
        "source_positions": ["十位", "个位"],
    },
)


@dataclass(frozen=True)
class FamilyMatrixCandidate:
    family_id: str
    atoms: tuple[str, ...]
    source_ref: str
    source_support_count: int
    source_risk_rate: float
    archive_positions: tuple[str, ...]
    archive_lotteries: tuple[str, ...]
    archive_classes: tuple[str, ...]
    play: str
    space_type: str
    rule_ref: str
    source_positions: tuple[str, ...]
    binding_basis: str
    pipeline_spec: dict
    pipeline_result: dict
    final_candidates: tuple[str, ...]

    @property
    def stage_count(self) -> int:
        return int(self.pipeline_result["stage_count"])

    @property
    def signature(self) -> tuple[str, ...]:
        return self.atoms

    def as_dict(self) -> dict:
        return {
            "family_id": self.family_id,
            "atoms": list(self.atoms),
            "source_ref": self.source_ref,
            "source_support_count": self.source_support_count,
            "source_risk_rate": self.source_risk_rate,
            "archive_positions": list(self.archive_positions),
            "archive_lotteries": list(self.archive_lotteries),
            "archive_classes": list(self.archive_classes),
            "play": self.play,
            "space_type": self.space_type,
            "rule_ref": self.rule_ref,
            "source_positions": list(self.source_positions),
            "binding_basis": self.binding_basis,
            "pipeline_spec": self.pipeline_spec,
            "pipeline_result": self.pipeline_result,
            "final_candidates": list(self.final_candidates),
            "paid_model_call": False,
            "registry_write": False,
            "website_write": False,
            "scheduled": False,
            "published": False,
        }


def _allowed_atoms_only(atoms: list[str]) -> bool:
    allowed = set(EXECUTABLE_ATOM_ORDER) | set(CONTEXT_ATOMS)
    return all(atom in allowed for atom in atoms)


def _ordered_executable_atoms(atoms: list[str]) -> tuple[str, ...]:
    return tuple(atom for atom in EXECUTABLE_ATOM_ORDER if atom in atoms)


def _executable_atoms(atoms: list[str]) -> tuple[str, ...] | None:
    if not _allowed_atoms_only(atoms):
        return None
    executable = _ordered_executable_atoms(atoms)
    if len(executable) not in {2, 3}:
        return None
    return executable


def _binding_for_family(family: dict) -> dict | None:
    positions = set(family.get("p") or [])
    for binding in PLAY_BINDINGS:
        if binding["position"] in positions:
            return binding
    return None


def _family_summary(family: dict, *, binding: dict | None = None) -> dict:
    atoms = list(family.get("a") or [])
    executable = list(_ordered_executable_atoms(atoms))
    result = {
        "family_id": str(family.get("f") or ""),
        "atoms": atoms,
        "executable_atoms": executable,
        "source_ref": next(iter(family.get("e") or []), None),
        "source_support_count": int(family.get("n") or 0),
        "source_risk_rate": float(family.get("r") or 0.0),
        "archive_positions": list(family.get("p") or []),
        "archive_lotteries": list(family.get("l") or []),
        "archive_classes": list(family.get("c") or []),
    }
    if binding:
        result.update(
            {
                "experimental_play": binding["play"],
                "space_type": binding["space_type"],
                "rule_ref": binding["rule_ref"],
                "binding_basis": "archive_position_mask_experimental_binding_not_source_play_claim",
            }
        )
    return result


def _passes_basic_source_gate(family: dict) -> bool:
    family_id = str(family.get("f") or "")
    if not family_id or family_id == TARGET_ALREADY_ACCEPTED_FAMILY:
        return False
    if int(family.get("n") or 0) < MIN_SOURCE_SUPPORT:
        return False
    if float(family.get("r") or 0.0) > MAX_SOURCE_RISK_RATE:
        return False
    if not ELIGIBLE_LOTTERIES.intersection(family.get("l") or []):
        return False
    if not [ref for ref in (family.get("e") or []) if str(ref)]:
        return False
    return True


def iter_eligible_family_matrix_candidates():
    for family in iter_brbcw_families() or []:
        if not _passes_basic_source_gate(family):
            continue

        family_id = str(family.get("f") or "")
        support = int(family.get("n") or 0)
        risk = float(family.get("r") or 0.0)
        atoms = _executable_atoms(list(family.get("a") or []))
        if atoms is None:
            continue
        source_refs = [str(ref) for ref in (family.get("e") or []) if str(ref)]
        binding = _binding_for_family(family)
        if binding is None:
            continue

        record = {
            "technique_family": family_id,
            "play": binding["play"],
            "technique_atoms": list(family.get("a") or []),
            "source_refs": source_refs,
            "source_support_count": support,
            "source_risk_rate": risk,
        }
        try:
            spec = build_real_knowledge_filter_pipeline(record)
            result = evaluate_filter_pipeline(spec)
            final_candidates = final_pipeline_candidate_strings(spec)
        except RealKnowledgePipelineError:
            continue

        if spec.get("space_type") != binding["space_type"]:
            continue
        if not final_candidates or len(final_candidates) != int(result["final_space"]):
            continue

        yield FamilyMatrixCandidate(
            family_id=family_id,
            atoms=atoms,
            source_ref=source_refs[0],
            source_support_count=support,
            source_risk_rate=risk,
            archive_positions=tuple(family.get("p") or []),
            archive_lotteries=tuple(family.get("l") or []),
            archive_classes=tuple(family.get("c") or []),
            play=binding["play"],
            space_type=binding["space_type"],
            rule_ref=binding["rule_ref"],
            source_positions=tuple(binding["source_positions"]),
            binding_basis="archive_position_mask_experimental_binding_not_source_play_claim",
            pipeline_spec=spec,
            pipeline_result=result,
            final_candidates=tuple(final_candidates),
        )


def build_real_knowledge_family_feasibility_report(*, near_limit: int = 12) -> dict:
    """Explain why the strict one-family matrix is or is not feasible.

    This scan intentionally keeps the original safety thresholds. It exposes the
    funnel instead of relaxing gates after a zero-result selection. It also
    surfaces safe *single-atom* source families, because those are the evidence
    needed to decide whether a later multi-source composition architecture is
    warranted.
    """
    families = list(iter_brbcw_families() or [])
    funnel = Counter()
    strict_candidates = list(iter_eligible_family_matrix_candidates())
    single_atom_pool: list[dict] = []
    multi_atom_without_position: list[dict] = []
    basic_gate_rows: list[dict] = []

    for family in families:
        funnel["total_families"] += 1
        family_id = str(family.get("f") or "")
        if family_id == TARGET_ALREADY_ACCEPTED_FAMILY:
            funnel["excluded_already_accepted"] += 1
            continue
        funnel["after_target_exclusion"] += 1

        if int(family.get("n") or 0) < MIN_SOURCE_SUPPORT:
            funnel["excluded_low_support"] += 1
            continue
        funnel["after_support"] += 1

        if float(family.get("r") or 0.0) > MAX_SOURCE_RISK_RATE:
            funnel["excluded_high_risk"] += 1
            continue
        funnel["after_risk"] += 1

        if not ELIGIBLE_LOTTERIES.intersection(family.get("l") or []):
            funnel["excluded_lottery"] += 1
            continue
        funnel["after_lottery"] += 1

        source_refs = [str(ref) for ref in (family.get("e") or []) if str(ref)]
        if not source_refs:
            funnel["excluded_no_example_source"] += 1
            continue
        funnel["after_source_ref"] += 1
        basic_gate_rows.append(_family_summary(family, binding=_binding_for_family(family)))

        atoms = list(family.get("a") or [])
        if not _allowed_atoms_only(atoms):
            funnel["excluded_contains_unbound_atom"] += 1
            continue
        funnel["deterministic_atoms_only"] += 1

        executable = _ordered_executable_atoms(atoms)
        if len(executable) == 1:
            funnel["deterministic_single_atom"] += 1
            binding = _binding_for_family(family)
            if binding:
                funnel["deterministic_single_atom_bindable"] += 1
                single_atom_pool.append(_family_summary(family, binding=binding))
            else:
                funnel["deterministic_single_atom_no_bindable_position"] += 1
            continue

        if len(executable) in {2, 3}:
            funnel["deterministic_multi_atom"] += 1
            binding = _binding_for_family(family)
            if binding:
                funnel["deterministic_multi_atom_bindable"] += 1
            else:
                funnel["deterministic_multi_atom_no_bindable_position"] += 1
                multi_atom_without_position.append(_family_summary(family))
            continue

        funnel["excluded_wrong_executable_atom_count"] += 1

    def sort_rows(rows: list[dict]) -> list[dict]:
        return sorted(
            rows,
            key=lambda row: (
                row["source_risk_rate"],
                -row["source_support_count"],
                row["family_id"],
            ),
        )

    single_atom_pool = sort_rows(single_atom_pool)
    multi_atom_without_position = sort_rows(multi_atom_without_position)
    basic_gate_rows = sort_rows(basic_gate_rows)

    single_atom_counts = Counter(
        row["executable_atoms"][0]
        for row in single_atom_pool
        if len(row.get("executable_atoms") or []) == 1
    )
    single_by_space = Counter(row.get("space_type") for row in single_atom_pool if row.get("space_type"))

    composition_ready_spaces = []
    for space_type in sorted(single_by_space):
        atoms = {
            row["executable_atoms"][0]
            for row in single_atom_pool
            if row.get("space_type") == space_type and len(row.get("executable_atoms") or []) == 1
        }
        if len(atoms) >= 2:
            composition_ready_spaces.append({"space_type": space_type, "distinct_atoms": sorted(atoms)})

    return {
        "status": "strict_single_family_matrix_feasibility_scanned",
        "strict_policy_unchanged": True,
        "funnel": dict(funnel),
        "strict_eligible_count": len(strict_candidates),
        "strict_matrix_feasible": len(strict_candidates) >= 3,
        "single_atom_pool_count": len(single_atom_pool),
        "single_atom_counts": dict(sorted(single_atom_counts.items())),
        "single_atom_space_counts": dict(sorted(single_by_space.items())),
        "composition_ready_spaces": composition_ready_spaces,
        "nearest_bindable_single_atom_families": single_atom_pool[:near_limit],
        "nearest_multi_atom_families_without_bindable_position": multi_atom_without_position[:near_limit],
        "basic_gate_examples": basic_gate_rows[:near_limit],
        "selection_policy": {
            "min_source_support": MIN_SOURCE_SUPPORT,
            "max_source_risk_rate": MAX_SOURCE_RISK_RATE,
            "eligible_lotteries": sorted(ELIGIBLE_LOTTERIES),
            "allowed_executable_atoms": list(EXECUTABLE_ATOM_ORDER),
            "allowed_stage_counts_for_single_family_matrix": [2, 3],
            "sample_dependent_atoms_allowed": False,
            "position_binding_is_source_play_claim": False,
            "binding_basis": "archive_position_mask_experimental_binding_not_source_play_claim",
        },
        "paid_model_call": False,
        "registry_write": False,
        "website_write": False,
        "scheduled": False,
        "published": False,
    }


def select_real_knowledge_family_matrix(limit: int = 5) -> list[FamilyMatrixCandidate]:
    if limit < 3 or limit > 5:
        raise RealKnowledgeFamilyMatrixError("matrix limit must be between 3 and 5")

    candidates = list(iter_eligible_family_matrix_candidates())
    if len(candidates) < 3:
        raise RealKnowledgeFamilyMatrixError(
            f"fewer than three safely executable real families found: {len(candidates)}"
        )

    candidates.sort(
        key=lambda item: (
            -item.stage_count,
            item.source_risk_rate,
            -item.source_support_count,
            item.family_id,
            item.space_type,
        )
    )

    selected: list[FamilyMatrixCandidate] = []
    signatures: set[tuple[str, ...]] = set()

    for desired_space in ("ordered_2digit", "ordered_3digit"):
        for item in candidates:
            if item.space_type != desired_space or item.signature in signatures:
                continue
            selected.append(item)
            signatures.add(item.signature)
            break

    for item in candidates:
        if len(selected) >= limit:
            break
        if item.signature in signatures:
            continue
        selected.append(item)
        signatures.add(item.signature)

    if len(selected) < 3:
        raise RealKnowledgeFamilyMatrixError(
            f"fewer than three structurally distinct safe families found: {len(selected)}"
        )
    return selected


def build_real_knowledge_family_matrix_report(limit: int = 5) -> dict:
    feasibility = build_real_knowledge_family_feasibility_report()
    if not feasibility["strict_matrix_feasible"]:
        return {
            **feasibility,
            "status": "strict_single_family_matrix_not_feasible",
            "selected_count": 0,
            "selected": [],
            "next_architecture_question": (
                "whether two or three independently source-backed single-atom families can be composed "
                "into one explicitly system-authored multistage experiment without presenting the composition "
                "as a source claim"
            ),
        }

    selected = select_real_knowledge_family_matrix(limit=limit)
    return {
        **feasibility,
        "status": "offline_matrix_selected",
        "selected_count": len(selected),
        "selected": [item.as_dict() for item in selected],
    }
