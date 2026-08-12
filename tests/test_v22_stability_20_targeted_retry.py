from __future__ import annotations

from copy import deepcopy

import pytest

import scripts.live_article_stability_20_retry_failed_v22 as runner


def test_targeted_retry_contains_exactly_seven_original_failures():
    prepared = runner.preflight_targets()
    ids = [blueprint["article_id"] for blueprint, _ in prepared]
    assert tuple(ids) == runner.TARGET_IDS
    assert len(ids) == 7
    for blueprint, packet in prepared:
        result = packet["practicality"]["filter_pipeline_result"]
        actual = [result["starting_space"]] + [stage["after_space"] for stage in result["stages"]]
        assert actual == runner.EXPECTED[blueprint["article_id"]]


def test_targeted_retry_does_not_include_any_first_pass_success():
    ids = set(runner.TARGET_IDS)
    first_pass_successes = {
        "LCM-STAB20-V22-011", "LCM-STAB20-V22-015", "LCM-STAB20-V22-016",
        "LCM-STAB20-V22-017", "LCM-STAB20-V22-019", "LCM-STAB20-V22-021",
        "LCM-STAB20-V22-022", "LCM-STAB20-V22-023", "LCM-STAB20-V22-024",
        "LCM-STAB20-V22-025", "LCM-STAB20-V22-026", "LCM-STAB20-V22-027",
        "LCM-STAB20-V22-028",
    }
    assert ids.isdisjoint(first_pass_successes)


def test_targeted_retry_fails_closed_on_pipeline_drift(monkeypatch):
    suite = runner.stability_suite_20()
    changed = deepcopy(suite)
    for item in changed:
        if item[0]["article_id"] == "LCM-STAB20-V22-014":
            item[1][-1] += 1
            break
    monkeypatch.setattr(runner, "stability_suite_20", lambda: changed)
    with pytest.raises(RuntimeError, match="frozen expected pipeline changed"):
        runner.preflight_targets()


def test_targeted_retry_fails_closed_if_target_missing(monkeypatch):
    suite = [item for item in runner.stability_suite_20() if item[0]["article_id"] != "LCM-STAB20-V22-020"]
    monkeypatch.setattr(runner, "stability_suite_20", lambda: suite)
    with pytest.raises(RuntimeError, match="targeted retry case missing"):
        runner.preflight_targets()
