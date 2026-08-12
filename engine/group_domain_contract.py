from __future__ import annotations

from collections import Counter
from itertools import combinations, product

from .knowledge_io import iter_brbcw_families
from .rules import load_rules

GROUP3_RULE_REF = "SSC-HIST-MECH-3STAR-GROUP3-V1"
GROUP6_RULE_REF = "SSC-HIST-MECH-3STAR-GROUP6-V1"
GROUP_ATOM = "group3_group6"
DAN_ATOM = "dan_candidate"


class GroupDomainContractError(ValueError):
    pass


def _rule_by_id(rule_id: str) -> dict:
    for rule in load_rules():
        if rule.get("rule_id") == rule_id:
            return rule
    raise GroupDomainContractError(f"required verified mechanics rule missing: {rule_id}")


def verified_group_rules() -> dict:
    group3 = _rule_by_id(GROUP3_RULE_REF)
    group6 = _rule_by_id(GROUP6_RULE_REF)
    expected = {
        GROUP3_RULE_REF: {
            "play": "后三组选3",
            "covered_ordered_outcomes_per_single_bet": 3,
        },
        GROUP6_RULE_REF: {
            "play": "后三组选6",
            "covered_ordered_outcomes_per_single_bet": 6,
        },
    }
    for rule in (group3, group6):
        rule_id = str(rule.get("rule_id"))
        if rule.get("status") != "verified":
            raise GroupDomainContractError(f"group mechanics rule is not verified: {rule_id}")
        if rule.get("scope", "full") not in {"mechanics", "full"}:
            raise GroupDomainContractError(f"group rule does not verify mechanics: {rule_id}")
        if rule.get("lottery") != "时时彩":
            raise GroupDomainContractError(f"historical group rule taxonomy changed unexpectedly: {rule_id}")
        if rule.get("play") != expected[rule_id]["play"]:
            raise GroupDomainContractError(f"group play changed unexpectedly: {rule_id}")
        if int(rule.get("covered_ordered_outcomes_per_single_bet") or 0) != expected[rule_id]["covered_ordered_outcomes_per_single_bet"]:
            raise GroupDomainContractError(f"group coverage changed unexpectedly: {rule_id}")
    return {"group3": group3, "group6": group6}


def classify_three_digit_structure(value: str) -> str:
    if len(value) != 3 or not value.isdigit():
        raise GroupDomainContractError("three-digit structure requires exactly three decimal digits")
    counts = sorted(Counter(value).values(), reverse=True)
    if counts == [3]:
        return "triple_same"
    if counts == [2, 1]:
        return "group3"
    if counts == [1, 1, 1]:
        return "group6"
    raise GroupDomainContractError("unreachable three-digit multiplicity structure")


def ordered_structure_counts() -> dict:
    counts = Counter(
        classify_three_digit_structure("".join(str(digit) for digit in digits))
        for digits in product(range(10), repeat=3)
    )
    return {
        "ordered_space": 1000,
        "group3_ordered_outcomes": counts["group3"],
        "group6_ordered_outcomes": counts["group6"],
        "triple_same_ordered_outcomes": counts["triple_same"],
    }


def group3_bet_units() -> list[tuple[int, int]]:
    """Return unordered group3 bet units as (repeated_digit, other_digit)."""
    return [
        (repeated_digit, other_digit)
        for repeated_digit in range(10)
        for other_digit in range(10)
        if repeated_digit != other_digit
    ]


def group6_bet_units() -> list[tuple[int, int, int]]:
    """Return unordered group6 bet units as sorted three-distinct-digit tuples."""
    return list(combinations(range(10), 3))


def group_domain_summary() -> dict:
    rules = verified_group_rules()
    ordered = ordered_structure_counts()
    group3_units = group3_bet_units()
    group6_units = group6_bet_units()
    group3_coverage = len(group3_units) * int(rules["group3"]["covered_ordered_outcomes_per_single_bet"])
    group6_coverage = len(group6_units) * int(rules["group6"]["covered_ordered_outcomes_per_single_bet"])
    if group3_coverage != ordered["group3_ordered_outcomes"]:
        raise GroupDomainContractError("group3 unordered-unit coverage does not match ordered domain")
    if group6_coverage != ordered["group6_ordered_outcomes"]:
        raise GroupDomainContractError("group6 unordered-unit coverage does not match ordered domain")
    if sum((ordered["group3_ordered_outcomes"], ordered["group6_ordered_outcomes"], ordered["triple_same_ordered_outcomes"])) != 1000:
        raise GroupDomainContractError("three-digit multiplicity partition is incomplete")
    return {
        **ordered,
        "group3_bet_units": len(group3_units),
        "group6_bet_units": len(group6_units),
        "group3_ordered_coverage": group3_coverage,
        "group6_ordered_coverage": group6_coverage,
        "rule_refs": [GROUP3_RULE_REF, GROUP6_RULE_REF],
        "domain_kind": "unordered_group_bet_units_with_ordered_outcome_coverage",
        "reader_lottery_label": "分分彩",
        "internal_rule_taxonomy": "时时彩",
        "provider_mapping_required": True,
    }


def require_group_mode(group_mode: str | None) -> str:
    mode = str(group_mode or "").strip().lower()
    aliases = {
        "group3": "group3",
        "组三": "group3",
        "组选3": "group3",
        "group6": "group6",
        "组六": "group6",
        "组选6": "group6",
    }
    if mode not in aliases:
        raise GroupDomainContractError(
            "group3_group6 archive atom is not executable until group_mode is explicitly bound to group3 or group6"
        )
    return aliases[mode]


def high_leverage_family_domain_diagnostic() -> dict:
    families = list(iter_brbcw_families() or [])
    group_rows = []
    dan_rows = []
    for family in families:
        atoms = list(family.get("a") or [])
        row = {
            "family_id": family.get("f"),
            "atoms": atoms,
            "positions": list(family.get("p") or []),
            "classes": list(family.get("c") or []),
            "source_support_count": int(family.get("n") or 0),
            "source_risk_rate": float(family.get("r") or 0.0),
            "source_refs": list(family.get("e") or []),
        }
        if GROUP_ATOM in atoms:
            group_rows.append({
                **row,
                "domain_contract_available": True,
                "family_executable": False,
                "blocker": "group_mode_unbound_in_compact_archive",
                "required_parameter": "group_mode=group3|group6",
            })
        if DAN_ATOM in atoms:
            dan_rows.append({
                **row,
                "domain_contract_available": False,
                "family_executable": False,
                "blocker": "dan_candidate_semantics_and_parameter_binding_missing",
                "required_parameters": [
                    "candidate_digit_set",
                    "containment_or_position_semantics",
                    "target_play_domain",
                ],
            })
    return {
        "status": "group_domain_contract_diagnostic_only",
        "group_domain": group_domain_summary(),
        "group_atom_family_count": len(group_rows),
        "dan_atom_family_count": len(dan_rows),
        "group_families": group_rows,
        "dan_families": dan_rows,
        "group_atom_executable": False,
        "dan_atom_executable": False,
        "current_filter_pipeline_whitelist_changed": False,
        "source_archive_limitation": (
            "compact family archive preserves atom/position/class/support/risk/example-source metadata but not the exact matched source phrase or bound group/dan parameters"
        ),
        "paid_model_call": False,
        "registry_write": False,
        "website_write": False,
        "scheduled": False,
        "published": False,
    }
