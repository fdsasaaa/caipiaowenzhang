from engine.text import fingerprint, jaccard, sha256_text


def test_hash_stable():
    assert sha256_text("abc") == sha256_text("abc")
    assert sha256_text("abc") != sha256_text("abcd")


def test_fingerprint_normalizes_spacing():
    assert fingerprint("分分彩 技巧", "定位胆") == fingerprint("分分彩技巧", "定位胆")


def test_jaccard():
    assert jaccard("定位胆遗漏杀号", "定位胆遗漏杀号") == 1.0
    assert jaccard("定位胆遗漏杀号", "完全不同内容") < 0.5
