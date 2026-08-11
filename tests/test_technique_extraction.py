from scripts.extract_technique_candidates import make_candidate, build_clusters


def test_extract_candidate_flags_unverified_profit_claims():
    taxonomy = {
        "canonical_atoms": {"omission_threshold": ["遗漏.*期"], "progressive_staking": ["倍投"]},
        "lottery_terms": {"时时彩": ["时时彩"]},
        "positions": ["个位"],
        "categories": {"遗漏": ["遗漏"], "倍投资金": ["倍投"]},
        "claim_risk_terms": ["稳赚"],
        "money_claim_terms": ["盈利"],
    }
    row = {
        "thread_id": 1,
        "title": "时时彩个位遗漏倍投",
        "classification": "遗漏",
        "keywords": "时时彩|个位|遗漏|倍投",
        "cleaned_content": "个位遗漏3期后开始倍投，声称90%命中并且稳赚盈利。",
        "url": "https://example.test/1",
    }
    c = make_candidate(row, taxonomy)
    assert c["verification_status"] == "unverified_source"
    assert c["publishable"] is False
    assert "omission_threshold" in c["technique_atoms"]
    assert "progressive_staking" in c["technique_atoms"]
    assert "percentage_claim" in c["risk_flags"]
    assert "稳赚" in c["risk_flags"]


def test_clusters_group_same_method_signature():
    base = {
        "source_classification": "遗漏", "technique_atoms": ["omission_threshold"],
        "positions": ["个位"], "lotteries": ["时时彩"], "risk_flags": [],
    }
    rows = [dict(base, source_id="S1"), dict(base, source_id="S2")]
    clusters = build_clusters(rows)
    assert len(clusters) == 1
    assert clusters[0]["source_count"] == 2
