from engine import rules
from engine.rule_gaps import gap_id


def test_rule_capability_separates_mechanics_and_economics(monkeypatch):
    monkeypatch.setattr(rules, "load_rules", lambda: [
        {"rule_id":"M1","scope":"mechanics","lottery":"时时彩","play":"定位胆","status":"verified"},
        {"rule_id":"E1","scope":"economics","provider_id":"p1","lottery":"时时彩","play":"定位胆","status":"verified"},
    ])
    cap = rules.rule_capability("p1", "时时彩", "定位胆")
    assert cap["mechanics_verified"] is True
    assert cap["economics_verified"] is True
    assert cap["mechanics_rule_refs"] == ["M1"]
    assert cap["economics_rule_refs"] == ["E1"]


def test_mechanics_can_exist_without_provider_economics(monkeypatch):
    monkeypatch.setattr(rules, "load_rules", lambda: [
        {"rule_id":"M1","scope":"mechanics","lottery":"时时彩","play":"定位胆","status":"verified"}
    ])
    cap = rules.rule_capability("unknown", "时时彩", "定位胆")
    assert cap["can_generate_rule_compliant_example"] is True
    assert cap["can_state_stake_payout_rebate"] is False


def test_rule_gap_id_is_stable():
    assert gap_id("economics", "时时彩", "定位胆", "p1") == gap_id("economics", "时时彩", "定位胆", "p1")
    assert gap_id("economics", "时时彩", "定位胆", "p1") != gap_id("mechanics", "时时彩", "定位胆")
