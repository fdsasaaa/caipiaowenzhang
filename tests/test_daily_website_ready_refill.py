from engine.daily_website_ready import load_daily_policy
from engine.daily_website_ready_refill import _mean, _status_for_ready


def test_refill_status_uses_final_public_r1_count():
    # V3: minimum=1 is the formal commit floor; 1+ articles are PASS_PARTIAL
    assert _status_for_ready(20, target=20, minimum=1) == "PASS_TARGET"
    assert _status_for_ready(14, target=20, minimum=1) == "PASS_PARTIAL_QUALITY_FIRST"
    assert _status_for_ready(8, target=20, minimum=1) == "PASS_PARTIAL_QUALITY_FIRST"
    assert _status_for_ready(1, target=20, minimum=1) == "PASS_PARTIAL_QUALITY_FIRST"
    assert _status_for_ready(0, target=20, minimum=1) == "BLOCKED_BELOW_MINIMUM"


def test_refill_policy_has_quality_preserving_hard_caps():
    policy = load_daily_policy()
    assert policy["target"] == 20
    assert policy["minimum"] == 1
    assert policy["operational_minimum"] == 10
    assert policy["maximum"] == 25
    assert policy["partial_batch_retention"] is True
    assert policy["max_refill_rounds"] >= 2
    assert policy["max_approved_parents_per_day"] >= policy["target"]
    assert policy["max_model_generation_attempts_per_day"] >= policy["max_approved_parents_per_day"]
    assert policy["quality_floor_may_be_lowered"] is False
    assert policy["public_release_required_to_count"] is True


def test_mean_is_stable_for_diagnostics():
    assert _mean([]) is None
    assert _mean([90, 95, 100]) == 95.0
