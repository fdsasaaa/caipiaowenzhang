from engine.generation_normalization import normalize_generation_metadata


def test_pure_editorial_scope_disclaimer_is_normalized_from_source_unverified():
    article = {
        "claim_evidence": [{
            "claim_text": "本文只讲分分彩五星直选的玩法和筛选步骤，不讨论未核验的平台经济参数。",
            "claim_type": "editorial",
            "support_type": "source_unverified",
            "support_refs": ["BRBCW-002590"],
            "evidence_note": "错误来源分类",
        }]
    }
    normalize_generation_metadata(article)
    row = article["claim_evidence"][0]
    assert row["support_type"] == "editorial"
    assert row["support_refs"] == []


def test_real_source_claim_is_never_reclassified():
    article = {
        "claim_evidence": [{
            "claim_text": "来源提到跨度筛选可作为一种经验方法，但本文不把它写成预测优势。",
            "claim_type": "editorial",
            "support_type": "source_unverified",
            "support_refs": ["BRBCW-002590"],
            "evidence_note": "来源边界",
        }]
    }
    normalize_generation_metadata(article)
    row = article["claim_evidence"][0]
    assert row["support_type"] == "source_unverified"
    assert row["support_refs"] == ["BRBCW-002590"]


def test_numeric_claim_is_never_reclassified():
    article = {
        "claim_evidence": [{
            "claim_text": "本文不讨论未核验参数，但这里有100个候选。",
            "claim_type": "editorial",
            "support_type": "source_unverified",
            "support_refs": ["BRBCW-002590"],
            "evidence_note": "numeric",
        }]
    }
    normalize_generation_metadata(article)
    assert article["claim_evidence"][0]["support_type"] == "source_unverified"
