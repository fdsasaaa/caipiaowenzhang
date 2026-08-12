from __future__ import annotations

from copy import deepcopy

import pytest

import scripts.live_article_stability_confirm_004_v22 as runner


def test_confirm_004_locks_original_case_and_pipeline():
    blueprint, packet = runner.preflight_target()
    assert blueprint["article_id"] == "LCM-STAB-V22-004"
    assert blueprint["play"] == "后三直选"
    assert blueprint["technique_atoms"] == ["compound_selection", "odd_even_filter"]
    result = packet["practicality"]["filter_pipeline_result"]
    actual = [result["starting_space"]] + [stage["after_space"] for stage in result["stages"]]
    assert actual == [1000, 216, 96]


def test_confirm_004_refuses_pipeline_drift(monkeypatch):
    suite = runner.stability_suite()
    changed = deepcopy(suite)
    changed[3][1][-1] += 1
    monkeypatch.setattr(runner, "stability_suite", lambda: changed)
    with pytest.raises(RuntimeError, match="frozen expected pipeline changed"):
        runner.preflight_target()


def test_confirm_004_refuses_technique_drift(monkeypatch):
    suite = runner.stability_suite()
    changed = deepcopy(suite)
    changed[3][0]["technique_atoms"] = ["sum_range"]
    monkeypatch.setattr(runner, "stability_suite", lambda: changed)
    with pytest.raises(RuntimeError, match="technique atoms changed"):
        runner.preflight_target()
