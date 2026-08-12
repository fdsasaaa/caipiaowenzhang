from __future__ import annotations

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


def _executable_atoms(atoms: list[str]) -> tuple[str, ...] | None:
    allowed = set(EXECUTABLE_ATOM_ORDER) | set(CONTEXT_ATOMS)
    if any(atom not in allowed for atom in atoms):
        return None
    executable = tuple(atom for atom in EXECUTABLE_ATOM_ORDER if atom in atoms)
    if len(executable) not in {2, 3}:
        return None
    return executable


def _binding_for_family(family: dict) -> dict | None:
    positions = set(family.get("p") or [])
    for binding in PLAY_BINDINGS:
        if binding["position"] in positions:
            return binding
    return None


def iter_eligible_family_matrix_candidates():
    for family in iter_brbcw_families() or []:
        family_id = str(family.get("f") or "")
        if not family_id or family_id == TARGET_ALREADY_ACCEPTED_FAMILY:
            continue

        support = int(family.get("n") or 0)
        risk = float(family.get("r") or 0.0)
        if support < MIN_SOURCE_SUPPORT or risk > MAX_SOURCE_RISK_RATE:
            continue
        if not ELIGIBLE_LOTTERIES.intersection(family.get("l") or []):
            continue

        atoms = _executable_atoms(list(family.get("a") or []))
        if atoms is None:
            continue
        source_refs = [str(ref) for ref in (family.get("e") or []) if str(ref)]
        if not source_refs:
            continue
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


def select_real_knowledge_family_matrix(limit: int = 5) -> list[FamilyMatrixCandidate]:
    if limit < 3 or limit > 5:
        raise RealKnowledgeFamilyMatrixError("matrix limit must be between 3 and 5")

    candidates = list(iter_eligible_family_matrix_candidates())
    if len(candidates) < 3:
        raise RealKnowledgeFamilyMatrixError(
            f"fewer than three safely executable real families found: {len(candidates)}"
        )

    # Prefer three-stage families, lower source-risk, stronger source support,
    # and then a stable family id. Family ids are atom-signature hashes, so
    # selecting unique ids also prevents duplicate atom structures.
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
    spaces: set[str] = set()

    # First pass seeks candidate-space diversity where available.
    for desired_space in ("ordered_2digit", "ordered_3digit"):
        for item in candidates:
            if item.space_type != desired_space or item.signature in signatures:
                continue
            selected.append(item)
            signatures.add(item.signature)
            spaces.add(item.space_type)
            break

    for item in candidates:
        if len(selected) >= limit:
            break
        if item.signature in signatures:
            continue
        selected.append(item)
        signatures.add(item.signature)
        spaces.add(item.space_type)

    if len(selected) < 3:
        raise RealKnowledgeFamilyMatrixError(
            f"fewer than three structurally distinct safe families found: {len(selected)}"
        )
    return selected


def build_real_knowledge_family_matrix_report(limit: int = 5) -> dict:
    eligible = list(iter_eligible_family_matrix_candidates())
    selected = select_real_knowledge_family_matrix(limit=limit)
    return {
        "status": "offline_matrix_selected",
        "selection_policy": {
            "min_source_support": MIN_SOURCE_SUPPORT,
            "max_source_risk_rate": MAX_SOURCE_RISK_RATE,
            "eligible_lotteries": sorted(ELIGIBLE_LOTTERIES),
            "allowed_executable_atoms": list(EXECUTABLE_ATOM_ORDER),
            "allowed_stage_counts": [2, 3],
            "sample_dependent_atoms_allowed": False,
            "position_binding_is_source_play_claim": False,
            "binding_basis": "archive_position_mask_experimental_binding_not_source_play_claim",
        },
        "eligible_count": len(eligible),
        "selected_count": len(selected),
        "selected": [item.as_dict() for item in selected],
        "paid_model_call": False,
        "registry_write": False,
        "website_write": False,
        "scheduled": False,
        "published": False,
    }
