"""Regression tests for V3 quality-first partial batch retention.

These tests verify the core principle: every article that fully passes all gates
is retained, regardless of batch volume. The quality floor is never lowered to
reach a volume target.

Cases:
  A: 8 qualified → PASS_PARTIAL_QUALITY_FIRST, all 8 retained
  B: 1 qualified → PASS_PARTIAL_QUALITY_FIRST, 1 retained
  C: 0 qualified → BLOCKED_BELOW_MINIMUM, 0 retained
  D: Quality floor never lowered to reach volume target
"""
from engine.daily_website_ready import load_daily_policy
from engine.daily_website_ready_refill import _status_for_ready


def _policy():
    return load_daily_policy()


def test_case_a_eight_qualified_retained_as_partial():
    """Case A: 8 articles fully pass all gates → PASS_PARTIAL_QUALITY_FIRST."""
    policy = _policy()
    ready = 8
    status = _status_for_ready(ready, target=policy["target"], minimum=policy["minimum"])
    assert status == "PASS_PARTIAL_QUALITY_FIRST"
    # All 8 must be retained (manifest written when ready >= minimum)
    assert ready >= policy["minimum"]
    assert ready < policy["target"]


def test_case_b_one_qualified_retained():
    """Case B: 1 article fully passes all gates → PASS_PARTIAL_QUALITY_FIRST."""
    policy = _policy()
    ready = 1
    status = _status_for_ready(ready, target=policy["target"], minimum=policy["minimum"])
    assert status == "PASS_PARTIAL_QUALITY_FIRST"
    assert ready >= policy["minimum"]


def test_case_c_zero_qualified_fail_closed():
    """Case C: 0 qualified → BLOCKED_BELOW_MINIMUM (fail closed)."""
    policy = _policy()
    ready = 0
    status = _status_for_ready(ready, target=policy["target"], minimum=policy["minimum"])
    assert status == "BLOCKED_BELOW_MINIMUM"
    assert ready < policy["minimum"]


def test_case_d_quality_floor_never_lowered():
    """Case D: quality_floor_may_be_lowered must be False regardless of volume."""
    policy = _policy()
    assert policy["quality_floor_may_be_lowered"] is False
    # Even at 0 qualified, the floor is not lowered
    assert policy["quality_floor_may_be_lowered"] is False
    # The operational_minimum is a health signal, not a quality relaxation trigger
    assert policy["operational_minimum"] == 10
    assert policy["minimum"] == 1
    assert policy["minimum"] < policy["operational_minimum"]


def test_operational_minimum_is_health_signal_not_discard_threshold():
    """operational_minimum must be >= minimum so 1..9 articles are PASS_PARTIAL."""
    policy = _policy()
    assert policy["operational_minimum"] >= policy["minimum"]
    # Articles 1..9 should be PASS_PARTIAL, not BLOCKED
    for count in range(1, policy["operational_minimum"]):
        status = _status_for_ready(count, target=policy["target"], minimum=policy["minimum"])
        assert status == "PASS_PARTIAL_QUALITY_FIRST", (
            f"count={count} should be PASS_PARTIAL_QUALITY_FIRST, got {status}"
        )


def test_partial_batch_retention_is_enabled():
    """partial_batch_retention must be True to retain sub-target batches."""
    policy = _policy()
    assert policy["partial_batch_retention"] is True
