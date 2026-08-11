from engine import quality


def _article():
    return {
        "title": "时时彩后二案例",
        "primary_keyword": "时时彩后二技巧",
        "content": "这是一个用于验证投注格式与覆盖率的示例。" * 30,
        "lottery": "时时彩",
        "play": "后二直选",
        "provider_id": "p1",
        "case_scope": "mechanics_only",
        "rule_refs": ["R1"],
        "information_gain_type": "worked_example",
    }


def test_quality_rejects_noncompliant_normalized_bets(monkeypatch):
    monkeypatch.setattr(quality, "rule_capability", lambda *args: {
        "mechanics_verified": True, "economics_verified": False
    })
    monkeypatch.setattr(quality, "duplicate_candidates", lambda article: [])
    article = _article()
    article["normalized_bets"] = [{
        "bet_id": "B1", "draw_id": "D1", "lottery_id": "L1", "play_id": "direct",
        "target_space_id": "LAST2", "target_space_size": 100,
        "covered_outcomes": [f"{x:02d}" for x in range(91)],
        "stake_amount": 1, "prize_amount": 100
    }]
    report = quality.evaluate(article)
    assert report.passed is False
    assert any("bet compliance failed" in error for error in report.errors)
