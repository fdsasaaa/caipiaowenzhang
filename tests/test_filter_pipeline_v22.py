from __future__ import annotations

import json
from pathlib import Path

from engine.ai_generation_v22 import build_multistage_generation_prompt
from engine.draft_pipeline_v22 import build_multistage_draft_packet
from engine.filter_pipeline import evaluate_filter_pipeline

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "agent" / "benchmarks" / "v22-live-batch"

EXPECTED = {
    "001-blueprint.json": (1000, [560, 384], [440, 176], 384),
    "002-blueprint.json": (1000, [375, 132], [625, 243], 132),
    "003-blueprint.json": (1000, [760, 588], [240, 172], 588),
    "004-blueprint.json": (45, [10, 7], [35, 3], 7),
    "005-blueprint.json": (45, [10, 6], [35, 4], 6),
}


def _load(name: str) -> dict:
    return json.loads((BENCH / name).read_text(encoding="utf-8"))


def test_all_five_v22_pipelines_have_exact_machine_enumerated_counts():
    for name, (start, afters, excluded, final) in EXPECTED.items():
        blueprint = _load(name)
        result = evaluate_filter_pipeline(blueprint["filter_pipeline_spec"])
        assert result["starting_space"] == start
        assert [stage["after_space"] for stage in result["stages"]] == afters
        assert [stage["excluded_space"] for stage in result["stages"]] == excluded
        assert result["final_space"] == final
        assert result["stage_count"] == 2


def test_v22_packet_carries_prefrozen_pipeline_into_case_and_practicality():
    blueprint = _load("001-blueprint.json")
    packet = build_multistage_draft_packet(blueprint)
    result = packet["practicality"]["filter_pipeline_result"]

    assert packet["contract_version"] == "2.2-multistage"
    assert packet["case_bundle"]["filter_pipeline_result"] == result
    assert result["starting_space"] == 1000
    assert result["final_space"] == 384
    assert packet["practicality"]["primary_filter_spec"]["after_filter_space"] == 384
    assert packet["practicality"]["minimum_concrete_steps"] >= 5


def test_v22_prompt_requires_all_stages_and_forbids_model_invented_extra_filter():
    blueprint = _load("004-blueprint.json")
    packet = build_multistage_draft_packet(blueprint)
    prompt = build_multistage_generation_prompt(packet)

    assert "V2.2 多层筛选合同" in prompt
    assert "候选数字池0/3/6/8/9" in prompt
    assert "45 -> 10" in prompt
    assert "对子和值8–15" in prompt
    assert "10 -> 7" in prompt
    assert "不得遗漏、换序或新增合同外阶段" in prompt
    assert "experimental_parameter" in prompt
