import pytest

from engine.article_angle_quality import evaluate_article_angle
from engine.article_angles import apply_article_angle


def _stage(index, atom, label, before, after, *, sample=False, params=None):
    return {
        "index": index,
        "atom": atom,
        "label": label,
        "before_space": before,
        "after_space": after,
        "excluded_space": before - after,
        "support_mode": "synthetic_case_calculation" if sample else "verified_rule_calculation",
        "params": params or {},
    }


def _base(stages):
    start = stages[0]["before_space"]
    final = stages[-1]["after_space"]
    return {
        "blueprint_id": "BP-base",
        "article_id": "LCM-IDEA-base000000000001",
        "fingerprint": "f" * 64,
        "angle_signature": "base-angle",
        "status": "ready_for_draft",
        "subject_lottery": "分分彩",
        "subject_play": "后三直选",
        "lottery": "时时彩",
        "play": "后三直选",
        "content_type": "technique_article",
        "site_category_key": "tzjq",
        "technique_atoms": [stage["atom"] for stage in stages],
        "primary_keyword": "分分彩后三直选和值跨度技巧",
        "secondary_keywords": [],
        "search_intent": "legacy",
        "slug_seed": "ffc-test",
        "case_structure": "selector=后三;metrics=sum,span;scope=mechanics_only",
        "production_filter_contract": {
            "mode": "multistage" if len(stages) > 1 else "single_stage",
            "filter_pipeline_result": {
                "starting_space": start,
                "final_space": final,
                "total_excluded": start - final,
                "stage_count": len(stages),
                "stages": stages,
            },
        },
    }


def _packet(variant):
    return {
        "article_angle_contract_version": variant["article_angle_contract_version"],
        "article_angle_contract": variant["article_angle_contract"],
    }


def _delivery(variant):
    c = variant["article_angle_contract"]
    m = c["required_machine_facts"]
    return {
        "angle_type": c["angle_type"],
        "reader_question": c["reader_question"],
        "deliverable_summary": c["required_deliverable"],
        "starting_space": m["starting_space"],
        "final_space": m["final_space"],
        "excluded_space": m["excluded_space"],
        "stage_count": m["stage_count"],
        "stage_labels": m["stage_labels"],
        "sample_stage_labels": m["sample_stage_labels"],
        "static_stage_labels": m["static_stage_labels"],
        "evidence_mode": m["evidence_mode"],
        "parameter_owner": "system_research",
        "source_parameter_attribution_allowed": False,
        "predictive_advantage_claimed": False,
        "stop_after_final_stage": True,
    }


def _article(variant, content, steps=None):
    return {
        "article_angle_contract_version": variant["article_angle_contract_version"],
        "information_gain_type": variant["information_gain_type"],
        "angle_delivery": _delivery(variant),
        "content": content,
        "practical_guidance": {"steps": steps or []},
    }


def test_legacy_packet_has_no_angle_gate():
    report = evaluate_article_angle({}, {"content": "legacy"})
    assert report.passed is True
    assert report.contracted is False
    assert report.score == 100


def test_space_math_requires_exact_machine_numbers_and_visible_calculation():
    variant = apply_article_angle(
        _base([_stage(1, "span_range", "跨度2–6", 1000, 436, params={"min": 2, "max": 6})]),
        "space_math",
    )
    article = _article(
        variant,
        "<h2>注数计算</h2><p>候选空间从1000个经过计算变成436个，一共排除564个。</p>",
    )
    report = evaluate_article_angle(_packet(variant), article)
    assert report.passed is True, report.errors
    article["angle_delivery"]["final_space"] = 435
    report = evaluate_article_angle(_packet(variant), article)
    assert report.passed is False
    assert any("final_space" in error for error in report.errors)


def test_execution_checklist_must_cover_each_contracted_stage():
    variant = apply_article_angle(
        _base([
            _stage(1, "sum_range", "和值8–19", 1000, 760, params={"min": 8, "max": 19}),
            _stage(2, "span_range", "跨度2–6", 760, 420, params={"min": 2, "max": 6}),
        ]),
        "execution_checklist",
    )
    article = _article(
        variant,
        "<h2>实际怎么操作</h2><p>按步骤执行和值8–19，再执行跨度2–6。</p>",
        ["1. 固定和值8–19", "2. 核对和值结果", "3. 执行跨度2–6", "4. 完成后停止"],
    )
    assert evaluate_article_angle(_packet(variant), article).passed is True
    article["practical_guidance"]["steps"] = ["1. 固定和值8–19", "2. 核对", "3. 完成", "4. 停止"]
    report = evaluate_article_angle(_packet(variant), article)
    assert report.passed is False
    assert any("跨度2–6" in error for error in report.errors)


def test_parameter_boundary_static_contract_must_deny_source_ownership():
    variant = apply_article_angle(
        _base([_stage(1, "span_range", "跨度2–6", 1000, 436, params={"min": 2, "max": 6})]),
        "parameter_boundary",
    )
    good = _article(
        variant,
        "<h2>参数设置</h2><p>这个参数是系统研究预设并先固定，不是来源推荐；来源只说明技巧家族来自哪里。</p>",
    )
    assert evaluate_article_angle(_packet(variant), good).passed is True
    bad = _article(variant, "<p>参数来自来源文章，按原文推荐设置。</p>")
    report = evaluate_article_angle(_packet(variant), bad)
    assert report.passed is False


def test_multistage_order_requires_contract_order():
    variant = apply_article_angle(
        _base([
            _stage(1, "sum_range", "和值8–19", 1000, 760),
            _stage(2, "span_range", "跨度2–6", 760, 420),
        ]),
        "multistage_order",
    )
    good = _article(
        variant,
        "<p>第1层和值8–19：从1000开始。第二层跨度2–6，最后得到420，合计排除580。</p>",
    )
    assert evaluate_article_angle(_packet(variant), good).passed is True
    bad = _article(
        variant,
        "<p>第1层先做跨度2–6，再做和值8–19；从1000最后得到420，排除580。</p>",
    )
    report = evaluate_article_angle(_packet(variant), bad)
    assert report.passed is False
    assert any("in order" in error for error in report.errors)


def test_sample_provenance_requires_explicit_non_predictive_boundary():
    variant = apply_article_angle(
        _base([
            _stage(1, "frequency_window", "近12期频率Top-5", 1000, 500, sample=True, params={"lookback": 12, "top_n": 5}),
        ]),
        "sample_provenance",
    )
    good = _article(
        variant,
        "<p>演示数据，不是真实开奖记录。近12期频率Top-5只是在演示样本上计算数字池，不代表预测，也不证明未来。</p>",
    )
    assert evaluate_article_angle(_packet(variant), good).passed is True
    bad = _article(
        variant,
        "<p>演示数据，不是真实开奖记录。近12期频率Top-5在样本上得到这组数字。</p>",
    )
    report = evaluate_article_angle(_packet(variant), bad)
    assert report.passed is False
    assert any("prediction" in error for error in report.errors)
