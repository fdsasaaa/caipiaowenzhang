from engine.compliance import validate_portfolio
from engine.target_spaces import expand_located_digits, normalized_direct_bet, normalized_located_bet


def test_located_expands_into_ordered_three_digit_space():
    covered = expand_located_digits(3, 2, [0, 1, 2, 3, 4])
    assert len(covered) == 500
    assert "000" in covered
    assert "999" not in covered


def test_located_plus_direct_can_form_full_cross_play_cover():
    located = normalized_located_bet(
        bet_id="A", draw_id="D1", lottery_id="L1", play_id="定位胆-个位",
        width=3, position_index=2, digits=[0, 1, 2, 3, 4],
        stake_amount=1, prize_amount=100, target_space_id="LAST3_ORDERED"
    )
    direct_tokens = [f"{x:03d}" for x in range(1000) if str(x).zfill(3)[-1] in "56789"]
    direct = normalized_direct_bet(
        bet_id="B", draw_id="D1", lottery_id="L1", play_id="后三直选单式",
        width=3, tokens=direct_tokens, stake_amount=1, prize_amount=100,
        target_space_id="LAST3_ORDERED"
    )
    report = validate_portfolio([located, direct])
    assert report.passed is False
    violation = next(v for v in report.violations if v["code"] == "cross_play_near_full_cover")
    assert violation["unique_covered_outcomes"] == 1000
    assert violation["coverage_ratio"] == 1.0
