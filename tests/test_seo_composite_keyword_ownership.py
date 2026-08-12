from engine.seo_keywords import method_keyword_labels, primary_keyword_for


def test_single_method_keyword_stays_natural_and_specific():
    assert primary_keyword_for("分分彩", "后三直选", ["sum_range"]) == "分分彩后三直选和值技巧"
    assert primary_keyword_for("分分彩", "后三直选", ["big_small_filter"]) == "分分彩后三直选大小技巧"


def test_composite_method_keyword_uses_up_to_three_stable_labels():
    atoms = ["odd_even_filter", "span_range", "sum_range", "frequency_window"]
    assert method_keyword_labels("后三直选", atoms) == ["和值", "跨度", "频率", "奇偶"]
    assert primary_keyword_for("分分彩", "后三直选", atoms) == "分分彩后三直选和值跨度频率技巧"


def test_atom_input_order_does_not_change_exact_primary_owner():
    a = ["sum_range", "span_range", "odd_even_filter"]
    b = list(reversed(a))
    assert primary_keyword_for("分分彩", "前三直选", a) == primary_keyword_for("分分彩", "前三直选", b)


def test_play_embedded_method_semantics_are_not_repeated():
    assert method_keyword_labels("后二大小单双", ["big_small_filter", "odd_even_filter"]) == []
    assert primary_keyword_for("分分彩", "后二大小单双", ["big_small_filter", "odd_even_filter"]) == "分分彩后二大小单双技巧"
