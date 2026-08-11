from engine.ai_generation import article_output_schema, build_generation_prompt
from engine.editorial_quality import evaluate_editorial


def _packet(editorial=True):
    packet = {
        "immutable_facts": {"technique_atoms": ["sum_range"]},
        "practicality": {"minimum_concrete_steps": 4},
    }
    if editorial:
        packet["editorial_contract_version"] = "1.0"
    return packet


def _article():
    return {
        "content": "<h2>实际怎么操作</h2><p>先固定参数，再从1000个结果筛到560个，排除440个。没有第二条已验证规则时停止继续添加条件。</p>",
        "practical_guidance": {
            "steps": [
                "固定起始空间。", "冻结主筛选参数。", "执行主筛选并记录变化。", "没有第二条已验证规则就停止。"
            ],
            "starting_space": "1000个有序结果",
            "after_primary_filter_space": "560个有序结果，排除440个",
            "parameter_freeze_rule": "先固定参数，再查看样本。",
            "stop_condition": "没有第二条已验证规则时停止继续添加过滤条件。",
            "next_step_policy": "只有新增条件存在已验证规则或明确证据且可复算时，才允许继续。",
        },
    }


def test_legacy_packet_remains_backward_compatible():
    report = evaluate_editorial(_packet(editorial=False), {"content": "legacy"})
    assert report.passed is True
    assert report.score == 100


def test_v21_practical_article_passes_reader_value_gate():
    report = evaluate_editorial(_packet(), _article())
    assert report.passed is True
    assert report.score == 100
    assert report.errors == []


def test_v21_missing_practical_guidance_is_blocked():
    report = evaluate_editorial(_packet(), {"content": "<p>只有原理，没有操作。</p>"})
    assert report.passed is False
    assert "practical_guidance" in report.errors[0]


def test_v21_filter_must_reduce_candidate_space():
    article = _article()
    article["practical_guidance"] = dict(article["practical_guidance"])
    article["practical_guidance"]["after_primary_filter_space"] = "1200个有序结果"
    report = evaluate_editorial(_packet(), article)
    assert report.passed is False
    assert any("actual reduction" in x for x in report.errors)


def test_v21_structured_output_requires_practical_guidance():
    schema = article_output_schema(_packet())
    assert "editorial_contract_version" in schema["required"]
    assert "practical_guidance" in schema["required"]
    prompt = build_generation_prompt(_packet())
    assert "没有第二条已验证规则" in prompt
    assert "practical_guidance" in prompt
