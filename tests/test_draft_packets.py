from engine.draft_packets import build_draft_packet, review_draft, synthetic_draws


def _blueprint():
    return {
        "blueprint_id": "BP-1",
        "article_id": "LCM-1",
        "provider_id": "p1",
        "lottery": "时时彩",
        "play": "后三直选",
        "content_type": "technique_article",
        "site_category_key": "tzjq",
        "technique_family": "F1",
        "technique_atoms": ["frequency_window", "sum_range"],
        "title": "时时彩后三直选技巧：频率与和值案例",
        "slug_seed": "ssc-last3-frequency-sum",
        "primary_keyword": "时时彩后三直选技巧",
        "secondary_keywords": ["时时彩技巧"],
        "search_intent": "学习具体投注技巧并看懂可复算案例",
        "information_gain_type": "method_mechanics_and_reproducible_case",
        "outline": ["玩法规则", "方法核心", "案例", "误区"],
        "case_structure": "selector=后三;metrics=frequency,sum;scope=mechanics_only",
        "case_scope": "mechanics_only",
        "rule_refs": ["R1"],
        "source_refs": ["S1"],
        "fingerprint": "abc123",
        "status": "ready_for_draft"
    }


def _article(packet, content):
    return {
        "article_id": "LCM-1",
        "title": packet["seo"]["title"],
        "slug": "ssc-last3-frequency-sum",
        "meta_description": packet["seo"]["meta_description"],
        "primary_keyword": packet["seo"]["primary_keyword"],
        "search_intent": packet["seo"]["search_intent"],
        "summary": "摘要",
        "content": content,
        "content_format": "html",
        "site_category_key": "tzjq",
        "rule_refs": ["R1"],
        "case_scope": "mechanics_only",
        "status": "draft"
    }


def test_synthetic_draws_are_deterministic():
    assert synthetic_draws(_blueprint()) == synthetic_draws(_blueprint())
    assert len(synthetic_draws(_blueprint())) == 16


def test_packet_contains_explicit_site_contract():
    packet = build_draft_packet(_blueprint())
    assert packet["status"] == "ready_for_ai_draft"
    assert packet["case_bundle"]["case_type"] == "synthetic_validation"
    assert packet["case_bundle"]["must_label_as"] == "演示数据，不是真实开奖记录"
    assert packet["claims"]["economics_allowed"] is False
    assert packet["immutable_facts"]["content_type"] == "technique_article"
    assert packet["immutable_facts"]["site_category_key"] == "tzjq"
    assert packet["immutable_facts"]["content_format"] == "html"
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


def test_review_requires_synthetic_label():
    packet = build_draft_packet(_blueprint())
    article = _article(packet, "<p>这是正文，但没有案例标签。</p>")
    report = review_draft(packet, article)
    assert report.passed is False
    assert any("synthetic case label missing" in x for x in report.errors)


def test_review_blocks_guarantee_language():
    packet = build_draft_packet(_blueprint())
    label = packet["case_bundle"]["must_label_as"]
    article = _article(packet, f"<p>{label}。这个方法必中。</p>")
    report = review_draft(packet, article)
    assert report.passed is False
    assert any("forbidden guaranteed-outcome term" in x for x in report.errors)


def test_review_blocks_changed_category_and_non_html():
    packet = build_draft_packet(_blueprint())
    label = packet["case_bundle"]["must_label_as"]
    article = _article(packet, f"<p>{label}。这里只做演示说明。</p>")
    article["site_category_key"] = "gjfa"
    article["content_format"] = "markdown"
    report = review_draft(packet, article)
    assert report.passed is False
    assert any("site_category_key differs" in x for x in report.errors)
    assert any("content_format differs" in x for x in report.errors)


def test_review_blocks_active_html_elements():
    packet = build_draft_packet(_blueprint())
    label = packet["case_bundle"]["must_label_as"]
    article = _article(packet, f"<p>{label}。案例说明。</p><script>alert(1)</script>")
    report = review_draft(packet, article)
    assert report.passed is False
    assert any("forbidden HTML element" in x for x in report.errors)
