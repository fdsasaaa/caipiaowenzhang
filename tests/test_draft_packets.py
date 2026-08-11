from engine.draft_packets import build_draft_packet, review_draft, synthetic_draws


def _blueprint():
    return {
        "blueprint_id": "BP-1",
        "article_id": "LCM-1",
        "provider_id": "p1",
        "lottery": "时时彩",
        "play": "后三直选",
        "technique_family": "F1",
        "technique_atoms": ["frequency_window", "sum_range"],
        "title": "时时彩后三直选技巧：频率与和值案例",
        "slug_seed": "ssc-last3-frequency-sum",
        "primary_keyword": "时时彩后三直选技巧",
        "secondary_keywords": ["时时彩技巧"],
        "search_intent": "学习具体投注技巧并看懂可复算案例",
        "outline": ["玩法规则", "方法核心", "案例", "误区"],
        "case_structure": "selector=后三;metrics=frequency,sum;scope=mechanics_only",
        "case_scope": "mechanics_only",
        "rule_refs": ["R1"],
        "source_refs": ["S1"],
        "fingerprint": "abc123",
        "status": "ready_for_draft"
    }


def test_synthetic_draws_are_deterministic():
    assert synthetic_draws(_blueprint()) == synthetic_draws(_blueprint())
    assert len(synthetic_draws(_blueprint())) == 16


def test_packet_contains_explicit_synthetic_case_label_and_no_economics():
    packet = build_draft_packet(_blueprint())
    assert packet["status"] == "ready_for_ai_draft"
    assert packet["case_bundle"]["case_type"] == "synthetic_validation"
    assert packet["case_bundle"]["must_label_as"] == "演示数据，不是真实开奖记录"
    assert packet["claims"]["economics_allowed"] is False
    assert "frequency" in packet["case_bundle"]


def test_packet_rejects_unready_blueprint():
    bp = _blueprint()
    bp["status"] = "blocked"
    try:
        build_draft_packet(bp)
    except ValueError as exc:
        assert "not ready_for_draft" in str(exc)
    else:
        raise AssertionError("expected blocked blueprint to be rejected")


def test_review_requires_synthetic_label_and_immutable_rule_refs():
    packet = build_draft_packet(_blueprint())
    article = {
        "article_id": "LCM-1",
        "title": packet["seo"]["title"],
        "slug": "x",
        "meta_description": packet["seo"]["meta_description"],
        "primary_keyword": packet["seo"]["primary_keyword"],
        "search_intent": packet["seo"]["search_intent"],
        "summary": "摘要",
        "content": "这是正文，但没有案例标签。",
        "rule_refs": ["R1"],
        "case_scope": "mechanics_only",
        "status": "draft"
    }
    report = review_draft(packet, article)
    assert report.passed is False
    assert any("synthetic case label missing" in x for x in report.errors)


def test_review_blocks_guarantee_language():
    packet = build_draft_packet(_blueprint())
    label = packet["case_bundle"]["must_label_as"]
    article = {
        "article_id": "LCM-1", "title": packet["seo"]["title"], "slug": "x",
        "meta_description": packet["seo"]["meta_description"], "primary_keyword": packet["seo"]["primary_keyword"],
        "search_intent": packet["seo"]["search_intent"], "summary": "摘要",
        "content": f"{label}。这个方法必中。", "rule_refs": ["R1"],
        "case_scope": "mechanics_only", "status": "draft"
    }
    report = review_draft(packet, article)
    assert report.passed is False
    assert any("forbidden guaranteed-outcome term" in x for x in report.errors)
