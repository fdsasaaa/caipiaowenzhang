from engine.format_rules import validate_format


def test_three_star_direct_single_and_compound_are_distinct():
    assert validate_format("前三", "直选单式", "079 707 796").passed
    assert not validate_format("前三", "直选单式", "089-145-689").passed
    assert validate_format("前三", "直选复式", "089-145-689").passed


def test_group3_and_group6_single_require_correct_digit_pattern():
    assert validate_format("前三", "组三单式", "007 011 778").passed
    assert not validate_format("前三", "组三单式", "023").passed
    assert validate_format("前三", "组六单式", "023 048 469").passed
    assert not validate_format("前三", "组六单式", "007").passed


def test_located_multi_position_differs_from_single_position():
    assert validate_format("定位胆", "定位胆", "458-578-569-178-056").passed
    assert not validate_format("定位胆", "定位胆", "5 7 9").passed
    assert validate_format("定位胆", "万位", "5 7 9").passed


def test_sum_values_keep_multidigit_atomic():
    report = validate_format("前三", "组选和值", "9 12 21")
    assert report.passed
    assert report.tokens == ["9", "12", "21"]


def test_dragon_tiger_requires_spaced_two_token_form():
    assert validate_format("龙虎", "龙虎", "龙 虎").passed
    assert not validate_format("龙虎", "龙虎", "龙虎").passed
