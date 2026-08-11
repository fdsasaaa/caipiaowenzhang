from engine import semantic_dedup


def _record(article_id, title, atoms, case_structure, play="后三直选"):
    return {
        "article_id": article_id,
        "title": title,
        "subject_lottery": "分分彩",
        "subject_play": play,
        "content_type": "technique_article",
        "technique_atoms": atoms,
        "case_structure": case_structure,
    }


def test_structural_duplicate_ignores_title_rewording(monkeypatch):
    old = _record(
        "OLD-1", "完全不同的旧标题", ["position_filter", "span_range"],
        "selector=后三;metrics=span,position_filter;scope=mechanics_only",
    )
    monkeypatch.setattr(semantic_dedup, "iter_registry", lambda name: iter([old]))
    candidate = _record(
        "NEW-1", "换一个标题讲后三号码", ["span_range", "position_filter"],
        "selector=后三;metrics=position_filter,span;scope=mechanics_only",
    )
    hits = semantic_dedup.structural_duplicate_candidates(candidate)
    assert hits
    assert hits[0].article_id == "OLD-1"
    assert hits[0].score >= 0.82
    assert "same_case_selector" in hits[0].reasons


def test_different_method_is_not_structural_duplicate(monkeypatch):
    old = _record(
        "OLD-2", "后三跨度", ["position_filter", "span_range"],
        "selector=后三;metrics=span;scope=mechanics_only",
    )
    monkeypatch.setattr(semantic_dedup, "iter_registry", lambda name: iter([old]))
    candidate = _record(
        "NEW-2", "定位胆遗漏", ["omission_threshold"],
        "selector=个位;metrics=omission;scope=mechanics_only", play="定位胆",
    )
    assert semantic_dedup.structural_duplicate_candidates(candidate) == []


def test_same_article_lifecycle_is_excluded(monkeypatch):
    old = _record("SAME", "旧状态", ["span_range"], "selector=后三;metrics=span;scope=mechanics_only")
    monkeypatch.setattr(semantic_dedup, "iter_registry", lambda name: iter([old]))
    candidate = _record("SAME", "新状态", ["span_range"], "selector=后三;metrics=span;scope=mechanics_only")
    assert semantic_dedup.structural_duplicate_candidates(candidate) == []
