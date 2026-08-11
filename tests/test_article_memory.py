from engine import article_memory


def _bp(status="ready_for_draft", article_id="LCM-IDEA-1"):
    return {
        "article_id": article_id,
        "blueprint_id": "BP-1",
        "provider_id": "p1",
        "title": "时时彩后三直选技巧：用遗漏阈值一步步筛选号码",
        "slug_seed": "时时彩-后三直选-omission_threshold",
        "primary_keyword": "时时彩后三直选技巧",
        "secondary_keywords": ["时时彩技巧"],
        "search_intent": "学习具体投注技巧并看懂可复算案例",
        "information_gain_type": "method_mechanics_and_reproducible_case",
        "lottery": "时时彩",
        "play": "后三直选",
        "technique_family": "F1",
        "technique_atoms": ["omission_threshold"],
        "angle_signature": "A1",
        "case_structure": "selector=后三;metrics=current_omission;scope=mechanics_only",
        "case_scope": "mechanics_only",
        "rule_refs": ["R1"],
        "source_refs": ["S1"],
        "fingerprint": "FP1",
        "status": status,
    }


def test_reserve_ready_blueprint(monkeypatch):
    written = []
    monkeypatch.setattr(article_memory, "known_article_ids", lambda: set())
    monkeypatch.setattr(article_memory, "duplicate_candidates", lambda candidate: [])
    monkeypatch.setattr(article_memory, "append_jsonl", lambda kind, record: written.append((kind, record)))
    result = article_memory.reserve_blueprints([_bp()])
    assert result["reserved_count"] == 1
    assert written[0][0] == "articles"
    assert written[0][1]["status"] == "idea"
    assert written[0][1]["fingerprint"] == "FP1"


def test_reservation_skips_blocked_or_existing(monkeypatch):
    written = []
    monkeypatch.setattr(article_memory, "known_article_ids", lambda: {"LCM-IDEA-EXISTING"})
    monkeypatch.setattr(article_memory, "duplicate_candidates", lambda candidate: [])
    monkeypatch.setattr(article_memory, "append_jsonl", lambda kind, record: written.append(record))
    result = article_memory.reserve_blueprints([
        _bp(status="blocked", article_id="LCM-IDEA-BLOCKED"),
        _bp(article_id="LCM-IDEA-EXISTING"),
    ])
    assert result["reserved_count"] == 0
    assert result["skipped_count"] == 2
    assert written == []


def test_reservation_rechecks_duplicate_at_write_time(monkeypatch):
    class Hit:
        article_id = "OLD-1"
    monkeypatch.setattr(article_memory, "known_article_ids", lambda: set())
    monkeypatch.setattr(article_memory, "duplicate_candidates", lambda candidate: [Hit()])
    monkeypatch.setattr(article_memory, "append_jsonl", lambda kind, record: (_ for _ in ()).throw(AssertionError("must not write")))
    result = article_memory.reserve_blueprints([_bp()])
    assert result["reserved_count"] == 0
    assert result["skipped"][0]["reason"] == "duplicate"
