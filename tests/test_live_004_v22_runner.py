from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from engine.draft_pipeline_v22 import build_multistage_draft_packet
from scripts.live_article_004_v22 import EXPECTED_PIPELINE, _assert_exact_case

ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = ROOT / "agent" / "benchmarks" / "v22-live-batch" / "004-blueprint.json"


def _blueprint() -> dict:
    return json.loads(BLUEPRINT.read_text(encoding="utf-8"))


def test_targeted_004_runner_accepts_only_exact_frozen_pipeline():
    blueprint = _blueprint()
    packet = build_multistage_draft_packet(blueprint)
    _assert_exact_case(packet, blueprint)
    result = packet["practicality"]["filter_pipeline_result"]
    assert result["starting_space"] == EXPECTED_PIPELINE["starting_space"]
    assert [stage["after_space"] for stage in result["stages"]] == EXPECTED_PIPELINE["stage_after_spaces"]
    assert result["final_space"] == EXPECTED_PIPELINE["final_space"]


def test_targeted_004_runner_refuses_changed_article_identity():
    blueprint = _blueprint()
    packet = build_multistage_draft_packet(blueprint)
    changed = deepcopy(blueprint)
    changed["article_id"] = "LCM-SMOKE-V22-999"
    with pytest.raises(RuntimeError, match="refuses any article"):
        _assert_exact_case(packet, changed)


def test_targeted_004_runner_refuses_changed_pipeline_before_paid_request():
    blueprint = _blueprint()
    packet = build_multistage_draft_packet(blueprint)
    changed_packet = deepcopy(packet)
    changed_packet["practicality"]["filter_pipeline_result"]["final_space"] = 8
    with pytest.raises(RuntimeError, match="refusing paid request"):
        _assert_exact_case(changed_packet, blueprint)
