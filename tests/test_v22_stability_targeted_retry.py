from __future__ import annotations

from copy import deepcopy

import pytest

import scripts.live_article_stability_retry_003_004_v22 as runner


def test_targeted_retry_contains_only_original_003_and_004():
    prepared = runner.preflight_targets()
    ids = [blueprint["article_id"] for blueprint, _ in prepared]
    assert ids == ["LCM-STAB-V22-003", "LCM-STAB-V22-004"]
    for blueprint, packet in prepared:
        result = packet["practicality"]["filter_pipeline_result"]
        actual = [result["starting_space"]] + [stage["after_space"] for stage in result["stages"]]
        assert actual == runner.EXPECTED[blueprint["article_id"]]


def test_targeted_retry_fails_closed_if_original_pipeline_changes(monkeypatch):
    original = runner.stability_suite()
    changed = deepcopy(original)
    # Change only case 004's recorded expectation; paid runner must refuse it.
    changed[3][1][-1] += 1
    monkeypatch.setattr(runner, "stability_suite", lambda: changed)
    with pytest.raises(RuntimeError, match="frozen expected pipeline changed"):
        runner.preflight_targets()


def test_targeted_retry_fails_closed_if_target_case_is_missing(monkeypatch):
    original = runner.stability_suite()
    changed = [item for item in original if item[0]["article_id"] != "LCM-STAB-V22-004"]
    monkeypatch.setattr(runner, "stability_suite", lambda: changed)
    with pytest.raises(RuntimeError, match="exactly 003 and 004"):
        runner.preflight_targets()
