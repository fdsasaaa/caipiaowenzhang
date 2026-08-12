from __future__ import annotations

from copy import deepcopy

from .draft_packets import build_draft_packet
from .filter_pipeline import evaluate_filter_pipeline


def build_multistage_draft_packet(blueprint: dict) -> dict:
    spec = blueprint.get("filter_pipeline_spec")
    result = evaluate_filter_pipeline(spec)

    packet = build_draft_packet(blueprint)
    packet = deepcopy(packet)
    packet["contract_version"] = "2.2-multistage"
    packet["case_bundle"]["filter_pipeline_spec"] = deepcopy(spec)
    packet["case_bundle"]["filter_pipeline_result"] = deepcopy(result)

    practicality = packet.setdefault("practicality", {})
    practicality["filter_pipeline_spec"] = deepcopy(spec)
    practicality["filter_pipeline_result"] = deepcopy(result)
    practicality["minimum_concrete_steps"] = max(
        int(practicality.get("minimum_concrete_steps", 4)),
        result["stage_count"] + 3,
    )
    practicality["must_follow_all_prefrozen_filter_stages"] = True
    practicality["reader_goal"] = (
        "读者看完后能从理论起始空间开始，按冻结顺序逐层复算每个过滤器，"
        "看到每层before/after/excluded，并在最后一层停止。"
    )

    # Existing V2.1 Editorial Gate understands one overall reduction. Feed it
    # the pipeline's total start -> final contraction while the V2.2 gate below
    # validates every individual stage.
    overall = {
        "selector": blueprint.get("resolved_selector"),
        "metric": "multi_stage_pipeline",
        "starting_space": result["starting_space"],
        "after_filter_space": result["final_space"],
        "excluded_space": result["total_excluded"],
        "basis": "prefrozen_multistage_contract",
    }
    practicality["primary_filter_spec"] = overall
    packet["case_bundle"]["primary_filter_spec"] = deepcopy(overall)
    return packet
