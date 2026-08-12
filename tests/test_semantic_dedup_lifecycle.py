from engine import semantic_dedup


def _candidate(article_id: str = "NEW-1") -> dict:
    return {
        "article_id": article_id,
        "fingerprint": "same-fingerprint",
        "title": "分分彩后三和值技巧",
        "subject_lottery": "分分彩",
        "subject_play": "后三直选",
        "content_type": "technique_article",
        "technique_atoms": ["sum_range"],
        "case_structure": "selector=后三;metrics=digit_sum;scope=mechanics_only",
    }


def test_rejected_revision_record_does_not_own_structural_space(monkeypatch):
    old = dict(_candidate("OLD-REJECTED"), status="rejected_for_revision")
    monkeypatch.setattr(semantic_dedup, "iter_registry", lambda kind: iter([old]))
    assert semantic_dedup.structural_duplicate_candidates(_candidate()) == []


def test_approved_record_still_owns_structural_space(monkeypatch):
    old = dict(_candidate("OLD-APPROVED"), status="approved")
    monkeypatch.setattr(semantic_dedup, "iter_registry", lambda kind: iter([old]))
    hits = semantic_dedup.structural_duplicate_candidates(_candidate())
    assert len(hits) == 1
    assert hits[0].article_id == "OLD-APPROVED"
    assert hits[0].reasons == ["same_fingerprint"]
