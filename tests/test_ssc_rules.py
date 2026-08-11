from engine.rules import verified_mechanics


def test_ssc_mechanics_baseline_has_core_plays():
    plays = {r["play"] for r in verified_mechanics("时时彩")}
    expected = {
        "一星直选", "后二直选", "后三直选", "五星直选",
        "后二组选", "后三组选3", "后三组选6", "定位胆", "后二大小单双",
    }
    assert expected.issubset(plays)


def test_alias_resolution():
    assert verified_mechanics("时时彩", "组三")[0]["play"] == "后三组选3"
    assert verified_mechanics("时时彩", "组六")[0]["play"] == "后三组选6"
    assert verified_mechanics("时时彩", "二星组选")[0]["play"] == "后二组选"
    assert verified_mechanics("时时彩", "个位定位胆")[0]["play"] == "一星直选"


def test_mechanics_do_not_inherit_historical_economics():
    for rule in verified_mechanics("时时彩"):
        if rule.get("lifecycle_status") == "historical_reference_only":
            assert rule.get("economics_inherited") is False
            assert rule.get("provider_mapping_required") is True
