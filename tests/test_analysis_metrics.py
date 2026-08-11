from engine.analysis_metrics import (
    current_omission, digit_sum, extract, frequency, has_neighbor_pair,
    parity_pattern, repeat_pattern, size_pattern, snapshot, span,
)

DRAWS = ["12345", "22346", "92347", "02348"]


def test_window_extraction_and_metrics():
    assert extract("12345", "后二") == (4, 5)
    assert extract("12345", "前三") == (1, 2, 3)
    assert extract("12345", "中三") == (2, 3, 4)
    assert digit_sum("12345", "后三") == 12
    assert span("12345", "后三") == 2
    assert parity_pattern("12345", "后三") == "单双单"
    assert size_pattern("12345", "后三") == "小小大"
    assert repeat_pattern("12345", "后三") == "组六"
    assert has_neighbor_pair("12345", "后三") is True


def test_frequency_and_current_omission():
    freq = frequency(DRAWS, "后二")
    assert freq[4] == 4
    assert freq[5] == 1 and freq[8] == 1
    omission = current_omission(DRAWS, "个位")
    assert omission[8] == 0
    assert omission[7] == 1
    assert omission[6] == 2
    assert omission[5] == 3
    assert omission[0] == 4


def test_repeat_patterns():
    assert repeat_pattern("11123", "前三") == "豹子"
    assert repeat_pattern("11234", "前三") == "组三"
    assert repeat_pattern("12345", "前三") == "组六"
    assert repeat_pattern("12344", "后二") == "重号"


def test_snapshot_is_reproducible():
    s = snapshot("12345", "后三")
    assert s.values == (3, 4, 5)
    assert s.sum_value == 12
    assert s.span_value == 2
