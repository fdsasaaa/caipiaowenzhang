from __future__ import annotations

from engine.editorial_quality import _explicit_stop_condition, evaluate_editorial


def _packet() -> dict:
    return {
        "editorial_contract_version": "1.1",
        "immutable_facts": {
            "technique_atoms": ["position_filter", "span_range"],
        },
        "practicality": {
            "minimum_concrete_steps": 4,
            "primary_filter_spec": {
                "starting_space": 100000,
                "after_filter_space": 43620,
                "excluded_space": 56380,
            },
        },
    }


def _article(stop_condition: str) -> dict:
    return {
        "content": (
            "<h2>实际怎么操作</h2>"
            "<p>五星直选从100000个有序结果开始，按系统预冻结的跨度2–6筛选后剩43620个，"
            "共排除56380个。</p>"
        ),
        "practical_guidance": {
            "steps": [
                "固定五星直选结果空间。",
                "在看演示数据前固定跨度2–6。",
                "逐个计算最大数字减最小数字。",
                "保留跨度落在2–6的结果并核对空间。",
            ],
            "starting_space": "五星直选共有100000个有序结果。",
            "after_primary_filter_space": "主筛选后剩43620个结果。",
            "parameter_freeze_rule": "跨度2–6由系统在观察演示样本前固定。",
            "stop_condition": stop_condition,
            "next_step_policy": "只有新增条件具有已验证规则或证据并且可以复算时，才允许继续缩小候选。",
        },
    }


def test_exact_rejected_v5_canary_stop_sentence_is_explicit_and_passes_editorial_gate():
    stop = "如果没有新增且已验证的规则或证据，就必须停在主筛选结果，不继续缩小候选。"
    assert _explicit_stop_condition(stop) is True
    report = evaluate_editorial(_packet(), _article(stop))
    assert report.passed is True, report.errors
    assert report.score == 100
    assert report.errors == []


def test_existing_explicit_stop_phrases_remain_accepted():
    for stop in (
        "完成这一层后停止。",
        "做到这里就停下。",
        "没有新证据就不再增加过滤器。",
        "没有新规则不得继续。",
        "没有新规则不要继续。",
        "没有新证据无需继续筛选。",
        "解释完成后到此为止。",
    ):
        assert _explicit_stop_condition(stop) is True, stop


def test_positive_continue_language_does_not_satisfy_stop_gate():
    stop = "如果没有新的已验证证据，也可以继续增加过滤器。"
    assert _explicit_stop_condition(stop) is False
    report = evaluate_editorial(_packet(), _article(stop))
    assert report.passed is False
    assert "stop_condition must explicitly tell the reader when to stop adding filters" in report.errors


def test_bare_stop_character_is_not_enough():
    assert _explicit_stop_condition("这里介绍何时停和何时继续。") is False
