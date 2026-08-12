from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean

from .knowledge_io import iter_brbcw_families
from .real_knowledge_family_matrix import (
    CONTEXT_ATOMS,
    ELIGIBLE_LOTTERIES,
    EXECUTABLE_ATOM_ORDER,
    MAX_SOURCE_RISK_RATE,
    MIN_SOURCE_SUPPORT,
    TARGET_ALREADY_ACCEPTED_FAMILY,
    _binding_for_family,
)
from .technique_semantics import load_semantics


# Conservative automation classes. These labels do not enable any atom.
# They only state what kind of contract would be required before implementation.
SAMPLE_PARAMETER_REQUIRED = {
    "cold_hot_split",
    "frequency_window",
    "omission_threshold",
}

# These already have a semantics definition that is a direct property of one
# candidate value/window and does not require observing historical samples to
# choose the rule. They still need an explicit filter-pipeline operator and tests.
DETERMINISTIC_SEMANTICS_READY = {
    "repeat_number",
    "neighbor_number",
}


def _basic_gate(family: dict) -> bool:
    if str(family.get("f") or "") in {"", TARGET_ALREADY_ACCEPTED_FAMILY}:
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


def automation_class(atom: str, semantics: dict) -> str:
    if atom in EXECUTABLE_ATOM_ORDER:
        return "already_executable"
    if atom in CONTEXT_ATOMS:
        return "context_only"
    if atom in DETERMINISTIC_SEMANTICS_READY and atom in semantics:
        return "deterministic_semantics_ready_needs_filter_operator"
    if atom in SAMPLE_PARAMETER_REQUIRED and atom in semantics:
        return "sample_parameter_contract_required"
    if atom in semantics:
        return "semantics_defined_manual_contract_review_required"
    return "missing_semantics_or_domain_contract"


def _would_be_structurally_executable(family: dict, added_atom: str, *, strict_multi: bool) -> bool:
    """Estimate structural unlock only; never claim the missing operator exists.

    A family counts only when adding exactly one atom would make every family atom
    either an existing executable atom, context atom, or that one proposed atom.
    It must also have a bindable 后二/后三 position. This deliberately avoids
    overstating unlock potential for families that still contain other unknown atoms.
    """
    atoms = set(str(atom) for atom in (family.get("a") or []) if str(atom))
    allowed = set(EXECUTABLE_ATOM_ORDER) | set(CONTEXT_ATOMS) | {added_atom}
    if not atoms.issubset(allowed):
        return False
    if _binding_for_family(family) is None:
        return False
    executable = [atom for atom in atoms if atom in set(EXECUTABLE_ATOM_ORDER) | {added_atom}]
    if strict_multi:
        return len(executable) in {2, 3}
    return len(executable) >= 1


def build_atom_gap_report() -> dict:
    families = list(iter_brbcw_families() or [])
    semantics = (load_semantics().get("atoms") or {})
    existing_allowed = set(EXECUTABLE_ATOM_ORDER) | set(CONTEXT_ATOMS)

    basic_rows = [family for family in families if _basic_gate(family)]
    blocked_rows = [
        family
        for family in basic_rows
        if any(str(atom) not in existing_allowed for atom in (family.get("a") or []))
    ]

    blocked_counts: Counter[str] = Counter()
    bindable_counts: Counter[str] = Counter()
    support_sums: Counter[str] = Counter()
    risks: dict[str, list[float]] = defaultdict(list)
    coexisting_existing_counts: Counter[str] = Counter()
    family_examples: dict[str, list[dict]] = defaultdict(list)

    for family in blocked_rows:
        atoms = [str(atom) for atom in (family.get("a") or []) if str(atom)]
        gaps = sorted(set(atom for atom in atoms if atom not in existing_allowed))
        has_existing_exec = any(atom in EXECUTABLE_ATOM_ORDER for atom in atoms)
        binding = _binding_for_family(family)
        for atom in gaps:
            blocked_counts[atom] += 1
            support_sums[atom] += int(family.get("n") or 0)
            risks[atom].append(float(family.get("r") or 0.0))
            if binding:
                bindable_counts[atom] += 1
            if has_existing_exec:
                coexisting_existing_counts[atom] += 1
            if len(family_examples[atom]) < 5:
                family_examples[atom].append({
                    "family_id": str(family.get("f") or ""),
                    "atoms": atoms,
                    "source_ref": next(iter(family.get("e") or []), None),
                    "source_support_count": int(family.get("n") or 0),
                    "source_risk_rate": float(family.get("r") or 0.0),
                    "positions": list(family.get("p") or []),
                    "classes": list(family.get("c") or []),
                    "experimental_play": binding["play"] if binding else None,
                })

    ranked = []
    for atom in sorted(blocked_counts):
        structural_bindable_unlock = sum(
            _would_be_structurally_executable(family, atom, strict_multi=False)
            for family in basic_rows
        )
        structural_strict_multi_unlock = sum(
            _would_be_structurally_executable(family, atom, strict_multi=True)
            for family in basic_rows
        )
        spec = semantics.get(atom) or {}
        ranked.append({
            "atom": atom,
            "automation_class": automation_class(atom, semantics),
            "semantics_defined": bool(spec),
            "metric": spec.get("metric"),
            "definition": spec.get("definition"),
            "safe_article_use": spec.get("safe_article_use"),
            "blocked_family_count": blocked_counts[atom],
            "bindable_blocked_family_count": bindable_counts[atom],
            "coexists_with_existing_executable_count": coexisting_existing_counts[atom],
            "source_support_sum": support_sums[atom],
            "average_source_risk_rate": round(mean(risks[atom]), 4) if risks[atom] else None,
            "structural_bindable_unlock_if_only_atom_added": structural_bindable_unlock,
            "structural_strict_multistage_unlock_if_only_atom_added": structural_strict_multi_unlock,
            "examples": family_examples[atom],
        })

    class_priority = {
        "deterministic_semantics_ready_needs_filter_operator": 0,
        "sample_parameter_contract_required": 1,
        "semantics_defined_manual_contract_review_required": 2,
        "missing_semantics_or_domain_contract": 3,
    }
    ranked.sort(key=lambda row: (
        class_priority.get(row["automation_class"], 9),
        -row["structural_strict_multistage_unlock_if_only_atom_added"],
        -row["structural_bindable_unlock_if_only_atom_added"],
        -row["bindable_blocked_family_count"],
        -row["blocked_family_count"],
        row["atom"],
    ))

    deterministic_candidates = [
        row for row in ranked
        if row["automation_class"] == "deterministic_semantics_ready_needs_filter_operator"
    ]
    sample_dependent = [
        row for row in ranked
        if row["automation_class"] == "sample_parameter_contract_required"
    ]

    return {
        "status": "real_knowledge_atom_gap_ranked_offline",
        "strict_policy_unchanged": True,
        "total_families": len(families),
        "basic_source_gate_families": len(basic_rows),
        "families_blocked_by_unbound_atoms": len(blocked_rows),
        "currently_executable_atoms": list(EXECUTABLE_ATOM_ORDER),
        "context_atoms": sorted(CONTEXT_ATOMS),
        "ranked_unbound_atoms": ranked,
        "deterministic_semantics_ready_candidates": deterministic_candidates,
        "sample_parameter_required_candidates": sample_dependent,
        "recommendation_policy": (
            "rank before implementation; a high frequency atom is not enabled automatically. "
            "Prefer deterministic semantics-ready atoms that can structurally unlock bindable families. "
            "Sample-dependent atoms require an explicit window/threshold provenance contract first."
        ),
        "paid_model_call": False,
        "registry_write": False,
        "website_write": False,
        "scheduled": False,
        "published": False,
    }
