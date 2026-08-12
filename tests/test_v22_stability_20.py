from __future__ import annotations

from copy import deepcopy

import pytest

import scripts.live_article_stability_20_v22 as runner
from engine.draft_pipeline_v22 import build_multistage_draft_packet
from engine.stability_suite_20_v22 import CASES, stability_suite_20
from engine.stability_suite_v22 import stability_suite as stability_suite_10


def _signature(blueprint: dict) -> tuple[str, tuple[str, ...]]:
    stages = blueprint["filter_pipeline_spec"]["stages"]
    return blueprint["play"], tuple(stage["op"] for stage in stages)


def test_stability_20_has_exactly_twenty_new_unique_cases():
    suite = stability_suite_20()
    assert len(suite) == 20
    ids = [blueprint["article_id"] for blueprint, _ in suite]
    keywords = [blueprint["primary_keyword"] for blueprint, _ in suite]
    assert len(set(ids)) == 20
    assert len(set(keywords)) == 20
    assert all(article_id.startswith("LCM-STAB20-V22-") for article_id in ids)


def test_stability_20_does_not_reuse_old_ten_ids_keywords_or_play_op_signatures():
    old = stability_suite_10()
    new = stability_suite_20()
    old_ids = {blueprint["article_id"] for blueprint, _ in old}
    old_keywords = {blueprint["primary_keyword"] for blueprint, _ in old}
    old_signatures = {_signature(blueprint) for blueprint, _ in old}
    new_ids = {blueprint["article_id"] for blueprint, _ in new}
    new_keywords = {blueprint["primary_keyword"] for blueprint, _ in new}
    new_signatures = {_signature(blueprint) for blueprint, _ in new}
    assert old_ids.isdisjoint(new_ids)
    assert old_keywords.isdisjoint(new_keywords)
    assert old_signatures.isdisjoint(new_signatures)


def test_stability_20_covers_all_five_play_windows_and_two_space_domains():
    suite = stability_suite_20()
    plays = {blueprint["play"] for blueprint, _ in suite}
    starts = {expected[0] for _, expected in suite}
    assert plays == {"后三直选", "前三直选", "中三直选", "后二组选", "前二组选"}
    assert starts == {45, 1000}
    assert sum(1 for _, expected in suite if expected[0] == 1000) == 12
    assert sum(1 for _, expected in suite if expected[0] == 45) == 8


def test_stability_20_contains_two_and_three_stage_articles():
    suite = stability_suite_20()
    stage_counts = [len(blueprint["filter_pipeline_spec"]["stages"]) for blueprint, _ in suite]
    assert set(stage_counts) == {2, 3}
    assert stage_counts.count(3) >= 8


def test_stability_20_uses_all_supported_filter_operators():
    operations = {
        stage["op"]
        for case in CASES
        for stage in case["stages"]
    }
    assert operations == {
        "sum_range", "span_range", "odd_count", "big_count", "distinct_count",
        "digit_pool", "pair_sum_range", "mixed_parity",
    }


def test_every_stability_20_pipeline_matches_frozen_expected_spaces():
    for blueprint, expected in stability_suite_20():
        packet = build_multistage_draft_packet(blueprint)
        result = packet["practicality"]["filter_pipeline_result"]
        actual = [result["starting_space"]] + [stage["after_space"] for stage in result["stages"]]
        assert actual == expected, blueprint["article_id"]
        assert result["final_space"] == expected[-1]
        assert all(stage["after_space"] < stage["before_space"] for stage in result["stages"])


def test_paid_stability_20_preflight_accepts_current_suite():
    prepared = runner.preflight_suite()
    assert len(prepared) == 20
    assert all(packet["contract_version"] == "2.2-multistage" for _, packet in prepared)


def test_paid_stability_20_preflight_fails_closed_on_pipeline_drift(monkeypatch):
    changed = deepcopy(stability_suite_20())
    changed[0][1][-1] += 1
    monkeypatch.setattr(runner, "stability_suite_20", lambda: changed)
    with pytest.raises(RuntimeError, match="refusing paid batch"):
        runner.preflight_suite()


def test_paid_stability_20_preflight_fails_closed_on_duplicate_keyword(monkeypatch):
    changed = deepcopy(stability_suite_20())
    changed[1][0]["primary_keyword"] = changed[0][0]["primary_keyword"]
    monkeypatch.setattr(runner, "stability_suite_20", lambda: changed)
    with pytest.raises(RuntimeError, match="duplicate or missing primary_keyword"):
        runner.preflight_suite()


def test_paid_stability_20_preflight_fails_closed_if_suite_count_changes(monkeypatch):
    changed = stability_suite_20()[:-1]
    monkeypatch.setattr(runner, "stability_suite_20", lambda: changed)
    with pytest.raises(RuntimeError, match="exactly 20"):
        runner.preflight_suite()
