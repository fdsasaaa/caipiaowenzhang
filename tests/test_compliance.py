from engine.compliance import assert_exportable, validate_portfolio


def _bet(bet_id, play_id, outcomes, stake=10, prize=100, phases=None):
    row = {
        "bet_id": bet_id,
        "draw_id": "D1",
        "lottery_id": "L1",
        "play_id": play_id,
        "target_space_id": "LAST2_ORDERED",
        "target_space_size": 100,
        "covered_outcomes": outcomes,
        "stake_amount": stake,
        "prize_amount": prize,
    }
    if phases is not None:
        row["phase_amounts"] = phases
    return row


def test_exactly_ninety_percent_is_allowed():
    report = validate_portfolio([_bet("A", "direct", [f"{x:02d}" for x in range(90)], stake=90)])
    assert report.passed is True


def test_low_money_but_over_coverage_is_blocked():
    report = validate_portfolio([_bet("A", "direct", [f"{x:02d}" for x in range(91)], stake=1)])
    assert report.passed is False
    assert any(v["code"] == "coverage_limit_exceeded" for v in report.violations)


def test_cross_play_union_deduplicates_and_blocks_near_full_cover():
    a = _bet("A", "located", [f"{x:02d}" for x in range(0, 50)], stake=1)
    b = _bet("B", "direct", [f"{x:02d}" for x in range(40, 95)], stake=1)
    report = validate_portfolio([a, b])
    assert report.passed is False
    hit = next(v for v in report.violations if v["code"] == "cross_play_near_full_cover")
    assert hit["unique_covered_outcomes"] == 95


def test_amount_over_limit_is_blocked():
    report = validate_portfolio([_bet("A", "direct", ["00"], stake=91)])
    assert any(v["code"] == "amount_limit_exceeded" for v in report.violations)


def test_advanced_staking_phase_is_checked():
    report = validate_portfolio([_bet("A", "direct", ["00"], phases={"p1": 10, "p2": 95})])
    assert any(v["code"] == "advanced_staking_amount_exceeded" for v in report.violations)


def test_missing_mapping_fails_closed():
    row = _bet("A", "direct", ["00"])
    del row["target_space_id"]
    report = validate_portfolio([row])
    assert report.passed is False
    assert report.violations[0]["code"] == "missing_target_space_mapping"


def test_export_gate_raises_on_violation():
    try:
        assert_exportable([_bet("A", "direct", [f"{x:02d}" for x in range(91)])])
    except ValueError as exc:
        assert "export blocked" in str(exc)
    else:
        raise AssertionError("expected export to be blocked")
