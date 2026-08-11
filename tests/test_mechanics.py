from engine.mechanics import (
    direct_hit, group2_hit, group3_hit, group6_hit,
    located_1d_hit, last2_property_hit,
)


def test_direct_hits():
    assert direct_hit("34", "34")
    assert not direct_hit("34", "43")
    assert direct_hit("12345", "12345")


def test_group2_covers_exactly_two_ordered_results():
    hits = [f"{i:02d}" for i in range(100) if group2_hit((3, 4), f"{i:02d}")]
    assert hits == ["34", "43"]


def test_group3_covers_exactly_three_ordered_results():
    hits = [f"{i:03d}" for i in range(1000) if group3_hit((1, 1, 7), f"{i:03d}")]
    assert hits == ["117", "171", "711"]


def test_group6_covers_exactly_six_ordered_results():
    hits = [f"{i:03d}" for i in range(1000) if group6_hit((1, 4, 7), f"{i:03d}")]
    assert hits == ["147", "174", "417", "471", "714", "741"]


def test_located_position_index_is_wan_to_ge():
    draw = "12345"
    assert located_1d_hit(0, 1, draw)
    assert located_1d_hit(4, 5, draw)
    assert not located_1d_hit(4, 4, draw)


def test_last2_property_probability_by_enumeration():
    size_hits = 0
    parity_hits = 0
    for i in range(100):
        draw = "000" + f"{i:02d}"
        size_hits += last2_property_hit("大", "小", draw, "大小")
        parity_hits += last2_property_hit("单", "双", draw, "单双")
    assert size_hits == 25
    assert parity_hits == 25
