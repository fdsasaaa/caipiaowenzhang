from engine import dedup, store


def _redirect_store(monkeypatch, tmp_path):
    registry = tmp_path / "registry"
    var = tmp_path / "var"
    files = {
        "articles": registry / "articles.jsonl",
        "techniques": registry / "techniques.jsonl",
        "sources": registry / "sources.jsonl",
    }
    monkeypatch.setattr(store, "REGISTRY", registry)
    monkeypatch.setattr(store, "VAR", var)
    monkeypatch.setattr(store, "DB", var / "index.sqlite3")
    monkeypatch.setattr(store, "REGISTRY_FILES", files)
    store.ensure_layout()
    return files


def test_registry_last_write_wins(monkeypatch, tmp_path):
    _redirect_store(monkeypatch, tmp_path)
    store.append_jsonl("articles", {"article_id": "A1", "title": "old", "status": "idea", "fingerprint": "FP1"})
    store.append_jsonl("articles", {"article_id": "A1", "title": "new", "status": "approved", "fingerprint": "FP1"})
    rows = list(store.iter_registry("articles"))
    assert len(rows) == 1
    assert rows[0]["status"] == "approved"
    assert rows[0]["title"] == "new"


def test_dedup_skips_same_article_lifecycle(monkeypatch):
    rows = [
        {"article_id": "A1", "title": "same", "fingerprint": "FP"},
        {"article_id": "A2", "title": "other", "fingerprint": "FP"},
    ]
    monkeypatch.setattr(dedup, "iter_registry", lambda kind: iter(rows))
    candidate = {"article_id": "A1", "title": "same", "fingerprint": "FP"}
    hits = dedup.duplicate_candidates(candidate)
    assert [x.article_id for x in hits] == ["A2"]
