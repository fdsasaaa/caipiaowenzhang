from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from engine.blueprints import blueprint_from_plan
from engine.draft_packets import build_case_bundle
from engine.production_controller import _public_subject, _verified_mechanics_work_units, load_controller_policy
from engine.production_filter_contract import ProductionFilterContractError, build_production_filter_contract
from engine.planner import plan_articles


def build_report(probe: int = 1000) -> dict:
    policy = load_controller_policy()
    reasons: Counter[str] = Counter()
    atom_sets: Counter[str] = Counter()
    play_reasons: dict[str, Counter[str]] = defaultdict(Counter)
    examples: dict[str, list[dict]] = defaultdict(list)
    plans_seen = 0
    ready_before_contract = 0
    blocked = 0
    passed = 0

    for unit in _verified_mechanics_work_units():
        result = plan_articles("", unit["lottery"], unit["play"], probe)
        for plan in result.get("plans", []):
            plans_seen += 1
            enriched = dict(plan)
            enriched["subject_lottery"] = _public_subject(unit["lottery"], policy)
            enriched["subject_play"] = unit["play"]
            blueprint = blueprint_from_plan(enriched)
            if blueprint.get("status") != "ready_for_draft":
                continue
            ready_before_contract += 1
            atoms = tuple(sorted(str(atom) for atom in (blueprint.get("technique_atoms") or []) if str(atom)))
            atom_key = "+".join(atoms)
            try:
                build_production_filter_contract(blueprint, build_case_bundle(blueprint))
            except ProductionFilterContractError as exc:
                blocked += 1
                reason = str(exc)
                reasons[reason] += 1
                atom_sets[atom_key] += 1
                play_reasons[unit["play"]][reason] += 1
                if len(examples[reason]) < 8:
                    examples[reason].append({
                        "article_id": blueprint.get("article_id"),
                        "play": unit["play"],
                        "selector": blueprint.get("resolved_selector"),
                        "family": blueprint.get("technique_family"),
                        "atoms": list(atoms),
                        "source_refs": blueprint.get("source_refs", []),
                        "error": reason,
                    })
                continue
            passed += 1

    return {
        "status": "strict-production-contract-block-diagnostic",
        "probe_per_work_unit": probe,
        "plans_seen": plans_seen,
        "ready_before_contract": ready_before_contract,
        "contract_passed_before_global_dedup": passed,
        "contract_blocked_before_global_dedup": blocked,
        "block_reasons": dict(reasons.most_common()),
        "blocked_atom_sets": dict(atom_sets.most_common()),
        "play_block_reasons": {
            play: dict(counter.most_common()) for play, counter in sorted(play_reasons.items())
        },
        "examples_by_reason": dict(examples),
        "provider_calls": 0,
        "registry_write": False,
        "website_write": False,
        "scheduled": False,
        "published": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose strict formal-production contract blocks without calling a model.")
    parser.add_argument("--probe", type=int, default=1000)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_report(args.probe)
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
