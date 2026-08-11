from engine.betmath import (
    direct_product,
    group2_banker_single,
    group2_pool,
    group3_group6_banker_single,
    group3_pool,
    group4_pool,
    group6_four_pool,
    group6_pool,
    group12_pool,
    group24_pool,
    group60_five_pool,
    group120_five_pool,
)


def test_three_star_counts():
    assert direct_product(10, 10, 10) == 1000
    assert group3_pool(10) == 90
    assert group6_pool(10) == 120
    assert group3_pool(10) + group6_pool(10) == 210
    assert group3_group6_banker_single(10) == 54


def test_two_star_counts():
    assert direct_product(10, 10) == 100
    assert group2_pool(10) == 45
    assert group2_banker_single(1, 10) == 9


def test_four_star_pattern_counts():
    assert direct_product(10, 10, 10, 10) == 10000
    assert group4_pool(10) == 90
    assert group6_four_pool(10) == 45
    assert group12_pool(10) == 360
    assert group24_pool(10) == 210


def test_five_star_derived_pattern_counts():
    assert direct_product(10, 10, 10, 10, 10) == 100000
    assert group60_five_pool(10) == 840
    assert group120_five_pool(10) == 252
