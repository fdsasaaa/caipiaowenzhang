from engine.claim_evidence import audit_claim_evidence


def _packet(case_scope="mechanics_only"):
    return {
        "immutable_facts": {
            "rule_refs": ["R1", "R2"],
            "source_refs": ["S1"],
            "case_scope": case_scope,
        }
    }


def _article(content, entries):
    return {
        "generation_contract_version": "2.0",
        "content": content,
        "claim_evidence": entries,
    }


def test_verified_rule_claim_must_reference_packet_rule():
    article = _article("<p>后二直选理论结果空间共100注。</p>", [{
        "claim_text": "后二直选理论结果空间共100注",
        "claim_type": "rule_fact",
        "support_type": "verified_rule",
        "support_refs": ["R1"],
        "evidence_note": "由已验证玩法规则支持",
    }])
    report = audit_claim_evidence(_packet(), article)
    assert report.passed is True


def test_hard_claim_without_evidence_is_blocked():
    report = audit_claim_evidence(_packet(), _article("<p>这个方法准确率95%。</p>", []))
    assert report.passed is False
    assert any("hard claim sentence lacks claim_evidence" in e for e in report.errors)


def test_unverified_source_claim_requires_qualification_and_source_ref():
    bad = _article("<p>来源文章声称准确率95%，但未验证。</p>", [{
        "claim_text": "准确率95%",
        "claim_type": "performance",
        "support_type": "source_unverified",
        "support_refs": ["S1"],
        "evidence_note": "来源原文观点",
    }])
    assert audit_claim_evidence(_packet(), bad).passed is False

    good = _article("<p>来源文章声称准确率95%，但未验证。</p>", [{
        "claim_text": "来源声称准确率95%，未验证",
        "claim_type": "performance",
        "support_type": "source_unverified",
        "support_refs": ["S1"],
        "evidence_note": "只转述来源观点",
    }])
    assert audit_claim_evidence(_packet(), good).passed is True


def test_economics_claim_blocked_in_mechanics_only():
    article = _article("<p>奖金数字这里只是声明。</p>", [{
        "claim_text": "奖金数字这里只是声明",
        "claim_type": "economics",
        "support_type": "verified_rule",
        "support_refs": ["R1"],
        "evidence_note": "测试",
    }])
    report = audit_claim_evidence(_packet("mechanics_only"), article)
    assert report.passed is False
    assert any("economics claim blocked" in e for e in report.errors)


def test_synthetic_case_must_reference_case_bundle_only():
    good = _article("<p>演示数据只用于展示计算。</p>", [{
        "claim_text": "演示数据只用于展示计算",
        "claim_type": "calculation",
        "support_type": "synthetic_case",
        "support_refs": ["case_bundle"],
        "evidence_note": "可复算演示",
    }])
    assert audit_claim_evidence(_packet(), good).passed is True
