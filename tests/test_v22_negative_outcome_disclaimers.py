from __future__ import annotations

from engine.claim_evidence import audit_claim_evidence


def _packet() -> dict:
    return {
        "immutable_facts": {
            "rule_refs": ["SSC-HIST-MECH-3STAR-LAST-V1"],
            "source_refs": [],
            "case_scope": "mechanics_only",
        }
    }


def _article(sentence: str) -> dict:
    return {
        "generation_contract_version": "2.0",
        "content": f"<p>{sentence}</p>",
        "claim_evidence": [],
    }


def test_live_case004_pure_negative_disclaimer_does_not_require_evidence():
    sentence = "样本本身只用于演示复算，不用于证明固定收益、固定胜率或其他未核验结论。"
    report = audit_claim_evidence(_packet(), _article(sentence))
    assert report.passed, report.errors


def test_numeric_rate_inside_negative_clause_still_requires_evidence():
    report = audit_claim_evidence(_packet(), _article("样本不用于证明胜率60%。"))
    assert not report.passed
    assert any("hard claim sentence lacks claim_evidence" in error for error in report.errors)


def test_mixed_negative_and_positive_rate_statement_still_requires_evidence():
    sentence = "这组样本不能证明胜率，但实际胜率更高。"
    report = audit_claim_evidence(_packet(), _article(sentence))
    assert not report.passed
    assert any("hard claim sentence lacks claim_evidence" in error for error in report.errors)


def test_plain_positive_rate_statement_still_requires_evidence():
    report = audit_claim_evidence(_packet(), _article("这个结构的胜率更高。"))
    assert not report.passed
