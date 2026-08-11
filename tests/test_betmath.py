from engine.betmath import (
    direct_product, group2_pool, group3_pool, group6_pool,
    located_1d_pool, theoretical_direct_probability,
)


def test_direct_product_counts():
    assert direct_product(2, 3) == 6
    assert direct_product(2, 3, 4) == 24
    assert direct_product(1, 1, 1, 1, 1) == 1


def test_group_pool_counts():
    assert group2_pool(10) == 45
    assert group3_pool(10) == 90
    assert group6_pool(10) == 120
    assert group2_pool(5) == 10
    assert group3_pool(5) == 20
    assert group6_pool(5) == 10


def test_located_and_direct_probabilities():
    assert located_1d_pool(8) == 8
    assert theoretical_direct_probability(1) == 0.1
    assert theoretical_direct_probability(2) == 0.01
    assert theoretical_direct_probability(3) == 0.001
    assert theoretical_direct_probability(5) == 0.00001
