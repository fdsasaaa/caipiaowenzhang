from __future__ import annotations

from copy import deepcopy

import pytest

import scripts.live_article_stability_10_v22 as runner
from engine.draft_pipeline_v22 import build_multistage_draft_packet
from engine.stability_suite_v22 import CASES, stability_suite


def test_stability_suite_has_ten_unique_cross_play_cases():
    suite = stability_suite()
    assert len(suite) == 10
    article_ids = [blueprint["article_id"] for blueprint, _ in suite]
    keywords = [blueprint["primary_keyword"] for blueprint, _ in suite]
    plays = {blueprint["play"] for blueprint, _ in suite}
    assert len(set(article_ids)) == 10
    assert len(set(keywords)) == 10
    assert plays == {"后三直选", "前三直选", "中三直选", "后二组选", "前二组选"}


def test_every_stability_pipeline_matches_frozen_expected_spaces():
    for blueprint, expected in stability_suite():
        packet = build_multistage_draft_packet(blueprint)
        result = packet["practicality"]["filter_pipeline_result"]
        actual = [result["starting_space"]] + [stage["after_space"] for stage in result["stages"]]
        assert actual == expected, blueprint["article_id"]
        assert result["final_space"] == expected[-1]
        assert result["stage_count"] == 2
        assert all(stage["after_space"] < stage["before_space"] for stage in result["stages"])


def test_expected_spaces_cover_ordered_and_unordered_domains():
    suite = stability_suite()
    starts = {expected[0] for _, expected in suite}
    assert starts == {45, 1000}
    assert sum(1 for _, expected in suite if expected[0] == 1000) == 6
    assert sum(1 for _, expected in suite if expected[0] == 45) == 4


def test_suite_uses_multiple_filter_families_not_title_variants_only():
    atom_pairs = {tuple(case["atoms"]) for case in CASES}
    operations = {stage["op"] for case in CASES for stage in case["stages"]}
    assert len(atom_pairs) >= 7
    assert {
        "sum_range", "span_range", "odd_count", "big_count", "distinct_count",
        "digit_pool", "pair_sum_range", "mixed_parity",
    }.issubset(operations)


def test_paid_runner_preflight_accepts_current_suite():
    prepared = runner.preflight_suite()
    assert len(prepared) == 10
    assert all(packet["contract_version"] == "2.2-multistage" for _, packet in prepared)


def test_paid_runner_preflight_fails_closed_on_pipeline_drift(monkeypatch):
    suite = stability_suite()
    changed = deepcopy(suite)
    changed[0][1][-1] += 1
    monkeypatch.setattr(runner, "stability_suite", lambda: changed)
    with pytest.raises(RuntimeError, match="refusing paid batch"):
        runner.preflight_suite()


def test_paid_runner_preflight_fails_closed_on_duplicate_keyword(monkeypatch):
    suite = stability_suite()
    changed = deepcopy(suite)
    changed[1][0]["primary_keyword"] = changed[0][0]["primary_keyword"]
    monkeypatch.setattr(runner, "stability_suite", lambda: changed)
    with pytest.raises(RuntimeError, match="duplicate or missing primary_keyword"):
        runner.preflight_suite()
