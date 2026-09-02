"""Policy invariant guard regression tests.

These tests prevent POLICY_OSCILLATION — the pattern where minimum flips
between 1 and 10 across PRs (#101 -> #102 -> #103 -> #104). If someone
reverts the policy to minimum=10 without also updating V3 fields, the
invariant guard must fail-fast BEFORE any AI generation budget is spent.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.daily_website_ready import (
    DailyProductionError,
    assert_v3_policy_invariant,
)


def _write_policy(tmp_path: Path, policy: dict) -> Path:
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(policy, ensure_ascii=False), encoding="utf-8")
    return path


GOOD_POLICY = {
    "version": 3,
    "timezone": "Asia/Singapore",
    "target": 20,
    "minimum": 1,
    "operational_minimum": 10,
    "maximum": 25,
    "candidate_pool": 40,
    "quality_first": True,
    "quality_floor_may_be_lowered": False,
    "partial_batch_retention": True,
    "public_release_required_to_count": True,
    "public_release_generation_attempts": 3,
    "public_release_timeout_seconds": 180,
    "public_release_min_plain_chars": 500,
    "public_release_min_h2": 3,
    "max_refill_rounds": 4,
    "refill_approved_batch_size": 20,
    "max_approved_parents_per_day": 80,
    "max_model_generation_attempts_per_day": 120,
    "model_preference_hints": ["mini"],
    "blocked_exact_primary_keywords": [],
    "blocked_primary_keyword_fragments": [],
    "frozen_article_ids": [],
    "forbidden_public_content_patterns": [],
    "required_uncertainty_terms_any": [],
    "forbidden_side_effects": [],
}


def test_invariant_guard_accepts_valid_v3_policy(tmp_path):
    path = _write_policy(tmp_path, GOOD_POLICY)
    policy = assert_v3_policy_invariant(path)
    assert policy["version"] == 3
    assert policy["minimum"] == 1


def test_invariant_guard_rejects_minimum_10_oscillation(tmp_path):
    """This is the core anti-oscillation test: if minimum is reverted to 10
    (the old discard-on-partial regime), the guard MUST fail."""
    bad = dict(GOOD_POLICY)
    bad["minimum"] = 10
    path = _write_policy(tmp_path, bad)
    with pytest.raises(DailyProductionError, match="POLICY_INVARIANT_VIOLATION"):
        assert_v3_policy_invariant(path)


def test_invariant_guard_rejects_version_2_regression(tmp_path):
    bad = dict(GOOD_POLICY)
    bad["version"] = 2
    bad["minimum"] = 10
    bad.pop("operational_minimum")
    bad.pop("partial_batch_retention")
    path = _write_policy(tmp_path, bad)
    with pytest.raises(DailyProductionError, match="POLICY_INVARIANT_VIOLATION"):
        assert_v3_policy_invariant(path)


def test_invariant_guard_rejects_missing_operational_minimum(tmp_path):
    bad = dict(GOOD_POLICY)
    bad.pop("operational_minimum")
    path = _write_policy(tmp_path, bad)
    with pytest.raises(DailyProductionError, match="operational_minimum is missing"):
        assert_v3_policy_invariant(path)


def test_invariant_guard_rejects_partial_batch_retention_false(tmp_path):
    bad = dict(GOOD_POLICY)
    bad["partial_batch_retention"] = False
    path = _write_policy(tmp_path, bad)
    with pytest.raises(DailyProductionError, match="partial_batch_retention must be true"):
        assert_v3_policy_invariant(path)


def test_invariant_guard_rejects_quality_floor_lowerable(tmp_path):
    bad = dict(GOOD_POLICY)
    bad["quality_floor_may_be_lowered"] = True
    path = _write_policy(tmp_path, bad)
    with pytest.raises(DailyProductionError, match="POLICY_INVARIANT_VIOLATION"):
        assert_v3_policy_invariant(path)


def test_invariant_guard_rejects_quality_first_false(tmp_path):
    bad = dict(GOOD_POLICY)
    bad["quality_first"] = False
    path = _write_policy(tmp_path, bad)
    with pytest.raises(DailyProductionError, match="POLICY_INVARIANT_VIOLATION"):
        assert_v3_policy_invariant(path)


def test_invariant_guard_reports_all_violations_at_once(tmp_path):
    """Guard should collect ALL violations, not fail on the first one,
    so the user sees the complete picture of what was reverted."""
    bad = dict(GOOD_POLICY)
    bad["version"] = 2
    bad["minimum"] = 10
    bad["quality_first"] = False
    bad["quality_floor_may_be_lowered"] = True
    bad["partial_batch_retention"] = False
    bad.pop("operational_minimum")
    path = _write_policy(tmp_path, bad)
    with pytest.raises(DailyProductionError) as exc_info:
        assert_v3_policy_invariant(path)
    msg = str(exc_info.value)
    assert "version" in msg.lower()
    assert "minimum is 10" in msg
    assert "operational_minimum" in msg
    assert "quality_first" in msg
    assert "quality_floor_may_be_lowered" in msg
    assert "partial_batch_retention" in msg
