"""Partial batch retention regression tests (Cases A-D).

V3 policy: qualified articles must NEVER be discarded just because they
don't reach the operational_minimum (10). The formal minimum is 1 — even
a single qualified article is retained and a manifest is written.
"""
from __future__ import annotations

from engine.daily_website_ready_refill import _status_for_ready


# Case A: 0 qualified → BLOCKED_BELOW_MINIMUM (fail closed)
def test_case_a_zero_qualified_blocks():
    status = _status_for_ready(0, target=20, minimum=1, operational_minimum=10)
    assert status == "BLOCKED_BELOW_MINIMUM"


# Case B: 1-9 qualified → PASS_PARTIAL_QUALITY_FIRST (retain all, no discard)
def test_case_b_one_qualified_is_retained():
    status = _status_for_ready(1, target=20, minimum=1, operational_minimum=10)
    assert status == "PASS_PARTIAL_QUALITY_FIRST"


def test_case_b_nine_qualified_is_retained():
    status = _status_for_ready(9, target=20, minimum=1, operational_minimum=10)
    assert status == "PASS_PARTIAL_QUALITY_FIRST"


# Case C: 10-19 qualified → PASS_PARTIAL_QUALITY_FIRST (at or above operational_minimum, retain all)
def test_case_c_ten_qualified_at_operational_minimum():
    status = _status_for_ready(10, target=20, minimum=1, operational_minimum=10)
    assert status == "PASS_PARTIAL_QUALITY_FIRST"


def test_case_c_nineteen_qualified():
    status = _status_for_ready(19, target=20, minimum=1, operational_minimum=10)
    assert status == "PASS_PARTIAL_QUALITY_FIRST"


# Case D: 20+ qualified → PASS_TARGET
def test_case_d_twenty_qualified_passes_target():
    status = _status_for_ready(20, target=20, minimum=1, operational_minimum=10)
    assert status == "PASS_TARGET"


def test_case_d_above_target():
    status = _status_for_ready(25, target=20, minimum=1, operational_minimum=10)
    assert status == "PASS_TARGET"


# Anti-oscillation: minimum=1 must never produce BLOCKED for >=1 qualified
def test_minimum_1_never_discards_qualified_articles():
    for count in range(1, 20):
        status = _status_for_ready(count, target=20, minimum=1, operational_minimum=10)
        assert status == "PASS_PARTIAL_QUALITY_FIRST", f"count={count} should be PASS_PARTIAL_QUALITY_FIRST, got {status}"


def test_minimum_1_never_discards_at_target():
    status = _status_for_ready(20, target=20, minimum=1, operational_minimum=10)
    assert status == "PASS_TARGET"


# Simulate old minimum=10 policy to ensure the guard catches it
def test_old_minimum_10_would_discard_qualified_articles():
    """This test documents the OLD behavior (minimum=10) that V3 fixes.
    With minimum=10, articles 1-9 would be BLOCKED and discarded.
    This test ensures that if someone reverts to minimum=10, the behavior
    changes in a way that the policy invariant guard will catch.
    """
    # With old minimum=10 (without operational_minimum parameter)
    old_status = _status_for_ready(6, target=20, minimum=10)
    assert old_status == "BLOCKED_BELOW_MINIMUM"

    # With V3 minimum=1
    v3_status = _status_for_ready(6, target=20, minimum=1, operational_minimum=10)
    assert v3_status == "PASS_PARTIAL_QUALITY_FIRST"

    # The key difference: V3 retains 6 qualified articles, old policy discards them
    assert v3_status != old_status
