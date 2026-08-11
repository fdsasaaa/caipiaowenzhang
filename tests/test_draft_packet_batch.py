from engine import draft_packets


def _bp(status, suffix):
    return {
        "blueprint_id": f"BP-{suffix}", "article_id": f"LCM-{suffix}", "provider_id": "p1",
        "lottery": "时时彩", "play": "后三直选", "content_type": "technique_article", "site_category_key": "tzjq",
        "technique_family": "F1", "technique_atoms": ["sum_range"], "title": "标题", "slug_seed": "slug",
        "primary_keyword": "时时彩后三直选技巧", "secondary_keywords": [],
        "search_intent": "学习", "information_gain_type": "method_mechanics_and_reproducible_case", "outline": ["规则", "案例"],
        "case_structure": "selector=后三;metrics=sum;scope=mechanics_only",
        "case_scope": "mechanics_only", "rule_refs": ["R1"], "source_refs": [],
        "fingerprint": f"fp-{suffix}", "status": status, "blockers": [] if status == "ready_for_draft" else ["x"]
    }


def test_batch_only_emits_ready_packets(monkeypatch):
    monkeypatch.setattr(draft_packets, "generate_blueprints", lambda *args, **kwargs: {
        "blueprints": [_bp("blocked", "1"), _bp("ready_for_draft", "2")]
    })
    result = draft_packets.generate_draft_packets("p1", "时时彩", "后三直选", 2)
    assert result["generated"] == 1
    assert result["packets"][0]["article_id"] == "LCM-2"
    assert result["packets"][0]["immutable_facts"]["site_category_key"] == "tzjq"
    assert result["skipped"][0]["status"] == "blocked"
