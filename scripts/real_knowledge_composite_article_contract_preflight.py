from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.real_knowledge_composite_article_contract import (
    build_composite_article_packet,
    build_composite_article_prompt,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline preflight for the cross-family sum/span article contract")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    packet = build_composite_article_packet()
    contract = packet["real_knowledge_composition"]
    result = packet["practicality"]["filter_pipeline_result"]
    prompt = build_composite_article_prompt()

    report = {
        "status": "offline_article_contract_ready",
        "article_id": packet["article_id"],
        "primary_keyword": packet["seo"]["primary_keyword"],
        "rule_refs": packet["immutable_facts"]["rule_refs"],
        "source_refs": packet["immutable_facts"]["source_refs"],
        "pipeline": {
            "starting_space": result["starting_space"],
            "stage_after_spaces": [stage["after_space"] for stage in result["stages"]],
            "stage_excluded_spaces": [stage["excluded_space"] for stage in result["stages"]],
            "final_space": result["final_space"],
            "total_excluded": result["total_excluded"],
        },
        "final_candidate_count": contract["final_candidate_count"],
        "final_candidate_sha256": contract["final_candidate_sha256"],
        "spot_checks": contract["spot_checks"],
        "must_list_all_final_candidates": contract["must_list_all_final_candidates"],
        "must_explain_how_to_test_any_candidate": contract["must_explain_how_to_test_any_candidate"],
        "prompt_contains_source_boundary": contract["source_boundary"] in prompt,
        "prompt_contains_order_boundary": contract["order_boundary"] in prompt,
        "prompt_contains_candidate_integrity_boundary": contract["candidate_integrity_boundary"] in prompt,
        "paid_model_call": False,
        "registry_write": False,
        "website_write": False,
        "scheduled": False,
        "published": False,
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
