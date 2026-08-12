from __future__ import annotations

import json

from engine.real_group6_article_contract import (
    ARTICLE_ID,
    DOMAIN_BOUNDARY,
    FAMILY_ID,
    PRIMARY_KEYWORD,
    SOURCE_BOUNDARY,
    SOURCE_REF,
    build_real_group6_article_packet,
    build_real_group6_article_prompt,
)
from engine.real_knowledge_family_matrix import EXECUTABLE_ATOM_ORDER


def build_preflight_summary() -> dict:
    packet = build_real_group6_article_packet()
    contract = packet["real_group6_validation"]
    binding = contract["binding"]

    checks = {
        "article_id": packet["article_id"] == ARTICLE_ID,
        "primary_keyword": packet["seo"]["primary_keyword"] == PRIMARY_KEYWORD,
        "family_id": packet["immutable_facts"]["technique_family"] == FAMILY_ID,
        "source_ref": packet["immutable_facts"]["source_refs"] == [SOURCE_REF],
        "rule_ref": packet["immutable_facts"]["rule_refs"] == ["SSC-HIST-MECH-3STAR-GROUP6-V1"],
        "group_mode": binding["group_mode"] == "group6",
        "system_mode_owner": binding["mode_provenance"]["owner"] == "system_research",
        "source_did_not_choose_mode": binding["source_did_not_choose_mode"] is True,
        "unit_domain": binding["candidate_unit_domain"] == "unordered_group_bet_units",
        "unit_count": binding["candidate_unit_count"] == 120,
        "ordered_structure_size": binding["ordered_structure_size_within_all_three_digit_outcomes"] == 720,
        "global_structure_share": binding["global_three_digit_structure_share"] == 0.72,
        "target_full_domain_coverage": binding["target_play_domain_coverage_if_all_units_used"] == 1.0,
        "coverage_ceiling": binding["target_coverage_ceiling_for_executable_portfolio"] == 0.90,
        "all_domain_execution_blocked": binding["all_domain_units_executable_portfolio_allowed"] is False,
        "normalized_bets_blocked": contract["normalized_bets_allowed"] is False,
        "global_whitelist_unchanged": "group3_group6" not in EXECUTABLE_ATOM_ORDER,
        "source_boundary_present": SOURCE_BOUNDARY in build_real_group6_article_prompt(),
        "domain_boundary_present": DOMAIN_BOUNDARY in build_real_group6_article_prompt(),
    }

    return {
        "ok": all(checks.values()),
        "stage": "real-group6-article-offline-preflight",
        "checks": checks,
        "article_id": ARTICLE_ID,
        "primary_keyword": PRIMARY_KEYWORD,
        "family_id": FAMILY_ID,
        "source_ref": SOURCE_REF,
        "group_mode": binding["group_mode"],
        "mode_owner": binding["mode_provenance"]["owner"],
        "rule_ref": binding["rule_ref"],
        "candidate_unit_domain": binding["candidate_unit_domain"],
        "candidate_unit_count": binding["candidate_unit_count"],
        "ordered_structure_size_within_all_three_digit_outcomes": binding["ordered_structure_size_within_all_three_digit_outcomes"],
        "global_three_digit_structure_share": binding["global_three_digit_structure_share"],
        "target_play_domain_coverage_if_all_units_used": binding["target_play_domain_coverage_if_all_units_used"],
        "target_coverage_ceiling_for_executable_portfolio": binding["target_coverage_ceiling_for_executable_portfolio"],
        "all_domain_units_executable_portfolio_allowed": binding["all_domain_units_executable_portfolio_allowed"],
        "provider_call": False,
        "registry_write": False,
        "website_write": False,
        "scheduled": False,
        "published": False,
    }


def main() -> int:
    summary = build_preflight_summary()
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
