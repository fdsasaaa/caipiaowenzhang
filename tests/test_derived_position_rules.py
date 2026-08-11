from engine.rules import verified_mechanics


def test_position_derived_direct_rules_exist():
    assert verified_mechanics("时时彩", "前二直选")[0]["positions"] == ["万位", "千位"]
    assert verified_mechanics("时时彩", "前三直选")[0]["positions"] == ["万位", "千位", "百位"]
    assert verified_mechanics("时时彩", "中三直选")[0]["positions"] == ["千位", "百位", "十位"]
    assert verified_mechanics("时时彩", "前四直选")[0]["positions"] == ["万位", "千位", "百位", "十位"]
    assert verified_mechanics("时时彩", "后四直选")[0]["positions"] == ["千位", "百位", "十位", "个位"]


def test_position_derived_group_rules_exist():
    assert verified_mechanics("时时彩", "前二组选")[0]["theoretical_single_bet_probability"] == "2/100 = 1/50"
    assert verified_mechanics("时时彩", "前三组三")[0]["covered_ordered_outcomes_per_single_bet"] == 3
    assert verified_mechanics("时时彩", "前三组六")[0]["covered_ordered_outcomes_per_single_bet"] == 6
    assert verified_mechanics("时时彩", "中三组三")[0]["covered_ordered_outcomes_per_single_bet"] == 3
    assert verified_mechanics("时时彩", "中三组六")[0]["covered_ordered_outcomes_per_single_bet"] == 6


def test_derived_rules_never_inherit_provider_economics():
    for rule in verified_mechanics("时时彩"):
        if rule.get("source_type") == "mathematical_position_window_derivation":
            assert rule.get("provider_mapping_required") is True
            assert rule.get("economics_inherited") is False
            assert rule.get("derivation_refs")
