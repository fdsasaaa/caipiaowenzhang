from engine import dedup


def test_duplicate_candidates_accepts_null_optional_fields(monkeypatch):
    monkeypatch.setattr(dedup, "iter_registry", lambda kind: iter([]))
    candidate = {
        "article_id": "GENERIC-1",
        "title": "通用格式文章",
        "primary_keyword": "投注格式",
        "search_intent": "了解格式",
        "lottery": None,
        "play": None,
        "technique_atoms": ["format_mechanics", None, "combination_counting"],
        "case_structure": None,
    }
    assert dedup.duplicate_candidates(candidate) == []


def test_duplicate_candidates_accepts_nulls_in_registry(monkeypatch):
    monkeypatch.setattr(dedup, "iter_registry", lambda kind: iter([
        {
            "article_id": "OLD-1",
            "title": None,
            "primary_keyword": None,
            "search_intent": None,
            "lottery": None,
            "play": None,
            "technique_atoms": None,
            "case_structure": None,
        }
    ]))
    candidate = {
        "article_id": "NEW-1",
        "title": "完全不同的新文章",
        "primary_keyword": "新关键词",
        "search_intent": "新意图",
        "lottery": None,
        "play": None,
        "technique_atoms": [],
        "case_structure": None,
    }
    assert dedup.duplicate_candidates(candidate) == []
