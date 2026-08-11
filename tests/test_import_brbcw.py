from scripts.import_brbcw import normalize


def test_manifest_does_not_include_full_text():
    row = {
        "thread_id": 1,
        "title": "测试",
        "classification": "杀号",
        "author": "a",
        "published_at": "2016-01-01",
        "url": "https://example.com/1",
        "keywords": "杀号",
        "quality_score": 10,
        "content_length": 4,
        "cleaned_content": "完整正文",
    }
    out = normalize(row)
    assert "cleaned_content" not in out
    assert out["claim_status"] == "unverified"
