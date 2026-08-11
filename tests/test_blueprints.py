from engine import blueprints


def _plan(case_ready=True):
    return {
        "provider_id": "p1",
        "lottery": "时时彩",
        "play": "后三直选",
        "technique_family": "F-OMISSION-SUM",
        "technique_atoms": ["omission_threshold", "sum_range"],
        "angle_signature": "ANGLE1",
        "positions": ["百位", "十位", "个位"],
        "source_refs": ["BRBCW-000001"],
        "source_support_count": 8,
        "source_risk_rate": 0.1,
        "status": "ready_mechanics_only",
        "rule_refs": ["SSC-HIST-MECH-3STAR-LAST-V1"],
        "allowed_case_scope": "mechanics_only",
        "case_plan": {
            "supported": [
                {"atom": "omission_threshold", "metric": "current_omission"},
                {"atom": "sum_range", "metric": "digit_sum"},
            ],
            "unsupported": [] if case_ready else ["carry_mapping"],
            "case_engine_ready": case_ready,
        },
    }


def test_blueprint_is_deterministic_and_seo_structured(monkeypatch):
    monkeypatch.setattr(blueprints, "duplicate_candidates", lambda candidate: [])
    a = blueprints.blueprint_from_plan(_plan())
    b = blueprints.blueprint_from_plan(_plan())
    assert a["fingerprint"] == b["fingerprint"]
    assert a["article_id"] == b["article_id"]
    assert a["status"] == "ready_for_draft"
    assert a["primary_keyword"] == "时时彩后三直选技巧"
    assert a["content_type"] == "technique_article"
    assert a["site_category_key"] == "tzjq"
    assert len(a["outline"]) >= 6
    assert "current_omission" in a["case_structure"]
    assert "digit_sum" in a["case_structure"]


def test_incomplete_case_semantics_blocks_drafting(monkeypatch):
    monkeypatch.setattr(blueprints, "duplicate_candidates", lambda candidate: [])
    bp = blueprints.blueprint_from_plan(_plan(case_ready=False))
    assert bp["status"] == "blocked"
    assert "technique_case_semantics_incomplete" in bp["blockers"]


def test_existing_article_overlap_blocks_before_draft(monkeypatch):
    class Hit:
        article_id = "OLD-1"
        title = "旧文章"
        score = 0.91
        reason = "lexical/core overlap"

    monkeypatch.setattr(blueprints, "duplicate_candidates", lambda candidate: [Hit()])
    bp = blueprints.blueprint_from_plan(_plan())
    assert bp["status"] == "duplicate_blocked"
    assert bp["duplicate_hits"][0]["article_id"] == "OLD-1"


def test_generate_blueprints_deduplicates_same_fingerprint(monkeypatch):
    plan = _plan()
    monkeypatch.setattr(blueprints, "plan_articles", lambda provider, lottery, play, count: {
        "status": "ready_mechanics_only", "plans": [plan, dict(plan)]
    })
    monkeypatch.setattr(blueprints, "duplicate_candidates", lambda candidate: [])
    result = blueprints.generate_blueprints("p1", "时时彩", "后三直选", 5)
    assert result["generated"] == 1
    assert result["ready"] == 1
