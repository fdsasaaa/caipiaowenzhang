from engine import dedup


def _candidate():
    return {
        "article_id": "NEW-1",
        "fingerprint": "same-fingerprint",
        "title": "分分彩后三和值技巧",
        "primary_keyword": "分分彩后三和值技巧",
        "search_intent": "学习具体投注技巧并看懂可复算案例",
        "subject_lottery": "分分彩",
        "subject_play": "后三直选",
        "technique_atoms": ["sum_range"],
        "case_structure": "selector=后三;metrics=digit_sum;scope=mechanics_only",
    }


def test_rejected_revision_record_does_not_own_duplicate_space(monkeypatch):
    old = dict(_candidate(), article_id="OLD-REJECTED", status="rejected_for_revision")
    monkeypatch.setattr(dedup, "iter_registry", lambda kind: iter([old]))
    assert dedup.duplicate_candidates(_candidate()) == []


def test_approved_record_still_owns_duplicate_space(monkeypatch):
    old = dict(_candidate(), article_id="OLD-APPROVED", status="approved")
    monkeypatch.setattr(dedup, "iter_registry", lambda kind: iter([old]))
    hits = dedup.duplicate_candidates(_candidate())
    assert len(hits) == 1
    assert hits[0].article_id == "OLD-APPROVED"
    assert hits[0].reason == "same fingerprint"
