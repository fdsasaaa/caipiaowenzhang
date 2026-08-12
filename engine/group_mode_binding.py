from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .group_domain_contract import (
    GROUP3_RULE_REF,
    GROUP6_RULE_REF,
    GroupDomainContractError,
    group3_bet_units,
    group6_bet_units,
    require_group_mode,
)
from .knowledge_io import iter_brbcw_families

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ARTICLES = ROOT / "knowledge" / "source_articles"
GROUP_ATOM = "group3_group6"

SOURCE_BINDING = "source_exact_phrase"
SYSTEM_BINDING = "system_research_prefrozen"
TARGET_COVERAGE_CEILING = 0.90


class GroupModeBindingError(ValueError):
    pass


def _family_by_id(family_id: str) -> dict:
    for family in iter_brbcw_families() or []:
        if family.get("f") == family_id:
            return family
    raise GroupModeBindingError(f"unknown BRBCW family: {family_id}")


def _canonical_units(mode: str) -> list[str]:
    if mode == "group3":
        return [f"{repeat}{repeat}{other}" for repeat, other in group3_bet_units()]
    if mode == "group6":
        return ["".join(str(digit) for digit in unit) for unit in group6_bet_units()]
    raise GroupModeBindingError(f"unsupported group mode: {mode}")


def _units_sha256(units: list[str]) -> str:
    return hashlib.sha256(("\n".join(units) + "\n").encode("utf-8")).hexdigest()


def _source_article_path(source_ref: str) -> Path:
    return SOURCE_ARTICLES / f"{source_ref}.json"


def _load_exact_source_evidence(source_ref: str) -> dict:
    path = _source_article_path(source_ref)
    if not path.exists():
        raise GroupModeBindingError(
            "source_exact_phrase binding requires a materialized source article under knowledge/source_articles; compact family metadata is insufficient"
        )
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GroupModeBindingError(f"invalid materialized source article: {source_ref}: {exc}") from exc
    if not isinstance(record, dict):
        raise GroupModeBindingError("materialized source article must be a JSON object")
    return record


def _source_text(record: dict) -> str:
    fields = ("title", "content", "text", "body", "excerpt")
    return "\n".join(str(record.get(field) or "") for field in fields)


def _exact_term_for_mode(mode: str) -> tuple[str, ...]:
    return ("组三", "组选3", "组选三") if mode == "group3" else ("组六", "组选6", "组选六")


def bind_group_mode(
    family_id: str,
    *,
    group_mode: str,
    binding_basis: str,
    source_ref: str | None = None,
    frozen_before_observation: bool = True,
) -> dict:
    family = _family_by_id(family_id)
    atoms = list(family.get("a") or [])
    if GROUP_ATOM not in atoms:
        raise GroupModeBindingError("family does not contain group3_group6 atom")
    try:
        mode = require_group_mode(group_mode)
    except GroupDomainContractError as exc:
        raise GroupModeBindingError(str(exc)) from exc

    if not frozen_before_observation:
        raise GroupModeBindingError("group mode must be frozen before any evaluation sample is inspected")

    representative_refs = [str(value) for value in (family.get("e") or []) if value]
    if binding_basis == SOURCE_BINDING:
        if not source_ref:
            raise GroupModeBindingError("source_exact_phrase binding requires source_ref")
        if source_ref not in representative_refs:
            raise GroupModeBindingError("source_ref is not the family representative provenance ref")
        record = _load_exact_source_evidence(source_ref)
        if str(record.get("source_id") or record.get("source_ref") or "") not in {"", source_ref}:
            raise GroupModeBindingError("materialized source record id does not match requested source_ref")
        text = _source_text(record)
        matched = [term for term in _exact_term_for_mode(mode) if term in text]
        if not matched:
            raise GroupModeBindingError(
                f"materialized source article does not explicitly contain a {mode} term; mode cannot be attributed to source"
            )
        mode_provenance = {
            "owner": "source",
            "source_ref": source_ref,
            "matched_terms": matched,
            "claim_boundary": "source explicitly names the group mode; mechanics still come from verified rule refs",
        }
    elif binding_basis == SYSTEM_BINDING:
        if source_ref is not None and source_ref not in representative_refs:
            raise GroupModeBindingError("optional source_ref must match family provenance when supplied")
        mode_provenance = {
            "owner": "system_research",
            "source_ref": representative_refs[0] if representative_refs else None,
            "matched_terms": [],
            "claim_boundary": (
                "family provenance supports only the broad group3_group6 technique atom; selected group_mode is a system research choice, not a source recommendation"
            ),
        }
    else:
        raise GroupModeBindingError(f"unsupported group binding basis: {binding_basis}")

    units = _canonical_units(mode)
    if mode == "group3":
        rule_ref = GROUP3_RULE_REF
        ordered_structure_size = len(units) * 3
    else:
        rule_ref = GROUP6_RULE_REF
        ordered_structure_size = len(units) * 6

    # Important denominator distinction:
    # - ordered_structure_size / 1000 describes how much of the complete ordered
    #   three-digit universe has this multiplicity structure;
    # - the candidate units listed here are the ENTIRE target play domain. If all
    #   units were actually bet, target-play coverage would be 100%, which violates
    #   the project's <=90% executable coverage rule. A mode binding is therefore
    #   descriptive/validation metadata, not an executable portfolio.
    global_structure_share = ordered_structure_size / 1000.0
    full_target_domain_coverage = 1.0

    return {
        "binding_status": "bound_for_validation",
        "family_id": family_id,
        "family_atoms": atoms,
        "family_source_refs": representative_refs,
        "group_mode": mode,
        "binding_basis": binding_basis,
        "mode_provenance": mode_provenance,
        "rule_ref": rule_ref,
        "candidate_unit_domain": "unordered_group_bet_units",
        "candidate_unit_count": len(units),
        "candidate_units_sha256": _units_sha256(units),
        "ordered_structure_size_within_all_three_digit_outcomes": ordered_structure_size,
        "all_three_digit_ordered_space": 1000,
        "global_three_digit_structure_share": global_structure_share,
        "target_play_unit_space": len(units),
        "target_play_domain_coverage_if_all_units_used": full_target_domain_coverage,
        "target_coverage_ceiling_for_executable_portfolio": TARGET_COVERAGE_CEILING,
        "all_domain_units_executable_portfolio_allowed": full_target_domain_coverage <= TARGET_COVERAGE_CEILING,
        "coverage_denominator_note": (
            "global_three_digit_structure_share is descriptive only; executable coverage must be measured against the selected play's own target domain"
        ),
        "frozen_before_observation": True,
        "reader_lottery_label": "分分彩",
        "internal_rule_taxonomy": "时时彩",
        "validation_only": True,
        "production_eligible": False,
        "source_did_not_choose_mode": binding_basis == SYSTEM_BINDING,
        "paid_model_call": False,
        "registry_write": False,
        "website_write": False,
        "scheduled": False,
        "published": False,
    }
