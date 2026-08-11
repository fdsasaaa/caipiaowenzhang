from engine.ai_generation import build_generation_prompt
from engine.claim_evidence import audit_claim_evidence


def _packet():
    return {
        "immutable_facts": {
            "rule_refs": ["R1"],
            "source_refs": ["S1"],
            "case_scope": "mechanics_only",
        }
    }


def _article(content: str, entries: list[dict]):
    return {
        "generation_contract_version": "2.0",
        "content": content,
        "claim_evidence": entries,
    }


def _rule_entry(claim: str):
    return {
        "claim_text": claim,
        "claim_type": "calculation",
        "support_type": "verified_rule",
        "support_refs": ["R1"],
        "evidence_note": "test evidence",
    }


def test_chinese_bet_count_is_a_hard_claim():
    report = audit_claim_evidence(_packet(), _article("<p>这个组合一共是三注。</p>", []))
    assert report.passed is False
    assert any("hard claim sentence lacks claim_evidence" in x for x in report.errors)


def test_chinese_percentage_is_a_hard_claim():
    report = audit_claim_evidence(_packet(), _article("<p>这个集合覆盖率是百分之六。</p>", []))
    assert report.passed is False
    assert any("hard claim sentence lacks claim_evidence" in x for x in report.errors)


def test_verbatim_hard_claim_evidence_passes():
    sentence = "这个组合一共是三注"
    report = audit_claim_evidence(_packet(), _article(f"<p>{sentence}。</p>", [_rule_entry(sentence)]))
    assert report.passed is True


def test_generation_prompt_requires_verbatim_hard_claim_registration():
    prompt = build_generation_prompt({})
    assert "claim_evidence.claim_text 必须复制该正文句子的完整文字" in prompt
    assert "中文数字写法" in prompt
    assert "每个硬声明句都要分别登记" in prompt
