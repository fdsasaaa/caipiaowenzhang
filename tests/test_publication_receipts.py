from __future__ import annotations

import copy

import pytest

from engine import publication_receipts
from engine.article_memory import get_article_record

ARTICLE_ID = "LCM-IDEA-48eb8743fbbbad11"
ARTICLE_KEY = "lcm-idea-48eb8743fbbbad11"
FINGERPRINT = "48eb8743fbbbad11b0758b4958ee60cd3c999123ffbaad0eb28c326a4fe71389"
CONTENT_HASH = "46206aa72fbd0c41445b287888b250888aedaa6ec23fc1084d16b47378ce3598"


def _receipt(cms_id: int = 321) -> dict:
    receipt = {
        "schema_version": 1,
        "receipt_type": "publication_receipt",
        "article_id": ARTICLE_ID,
        "article_key": ARTICLE_KEY,
        "fingerprint": FINGERPRINT,
        "content_hash": CONTENT_HASH,
        "cms_id": cms_id,
        "published_url": f"https://www.laocaimi.org/index.php?c=show&id={cms_id}",
        "published_at": "2026-08-11T14:30:00+00:00",
        "publisher_article_hash": "b" * 64,
        "source_file": ARTICLE_KEY + ".json",
        "site_base_url": "https://www.laocaimi.org",
    }
    receipt["receipt_id"] = publication_receipts.publication_receipt_id(receipt)
    return receipt


def _current(status: str = "approved") -> dict:
    return {
        "article_id": ARTICLE_ID,
        "status": status,
        "fingerprint": FINGERPRINT,
        "content_hash": CONTENT_HASH,
        "website_draft_path": f"content/drafts/{ARTICLE_KEY}.json",
        "published_url": None,
        "published_at": None,
    }


def _rehash(receipt: dict) -> dict:
    receipt["receipt_id"] = publication_receipts.publication_receipt_id(receipt)
    return receipt


def test_real_current_registry_record_accepts_matching_receipt_preview_only():
    current = get_article_record(ARTICLE_ID)
    assert current is not None
    assert current["status"] == "approved"
    assert current["fingerprint"] == FINGERPRINT
    assert current["content_hash"] == CONTENT_HASH
    assert current["website_draft_path"].endswith(ARTICLE_KEY + ".json")

    validated = publication_receipts.validate_publication_receipt(_receipt(), current=current)
    assert validated["article_id"] == ARTICLE_ID
    assert validated["cms_id"] == 321
    assert validated["published_url"] == "https://www.laocaimi.org/index.php?c=show&id=321"

    before = copy.deepcopy(current)
    preview = publication_receipts.import_publication_receipt(_receipt(), record=False)
    after = get_article_record(ARTICLE_ID)
    assert preview["status"] == "validated"
    assert preview["recorded"] is False
    assert preview["registry_record"]["status"] == "published"
    assert preview["registry_record"]["published_url"].endswith("id=321")
    assert after == before


def test_record_true_appends_published_state_only_after_validation(monkeypatch):
    calls = []
    monkeypatch.setattr(publication_receipts, "get_article_record", lambda article_id: _current())

    def fake_append(article_id, status, changes):
        calls.append((article_id, status, changes))
        return {**_current(), **changes, "article_id": article_id, "status": status}

    monkeypatch.setattr(publication_receipts, "append_article_state", fake_append)
    result = publication_receipts.import_publication_receipt(_receipt(), record=True)
    assert result["status"] == "recorded"
    assert result["recorded"] is True
    assert calls and calls[0][0] == ARTICLE_ID
    assert calls[0][1] == "published"
    assert calls[0][2]["cms_id"] == 321
    assert calls[0][2]["published_url"] == "https://www.laocaimi.org/index.php?c=show&id=321"
    assert calls[0][2]["publication_receipt_id"] == _receipt()["receipt_id"]


def test_exact_already_published_receipt_is_idempotent(monkeypatch):
    receipt = _receipt()
    current = {
        **_current("published"),
        "cms_id": 321,
        "published_url": receipt["published_url"],
        "published_at": receipt["published_at"],
        "publication_receipt_id": receipt["receipt_id"],
    }
    monkeypatch.setattr(publication_receipts, "get_article_record", lambda article_id: current)
    monkeypatch.setattr(
        publication_receipts,
        "append_article_state",
        lambda *args, **kwargs: pytest.fail("idempotent receipt must not append another registry state"),
    )
    result = publication_receipts.import_publication_receipt(receipt, record=True)
    assert result["status"] == "unchanged"
    assert result["recorded"] is False


@pytest.mark.parametrize(
    "mutator, message",
    [
        (lambda r: r.update({"fingerprint": "0" * 64}), "fingerprint does not match registry"),
        (lambda r: r.update({"content_hash": "0" * 64}), "content_hash does not match registry"),
        (lambda r: r.update({"article_key": "different-key", "source_file": "different-key.json"}), "article_key does not match website_draft_path"),
        (lambda r: r.update({"cms_id": 322}), "published_url does not match cms_id/site_base_url"),
        (lambda r: r.update({"published_at": "2026-08-11T14:30:00"}), "published_at must include timezone"),
        (lambda r: r.update({"receipt_id": "0" * 64}), "receipt_id does not match"),
    ],
)
def test_receipt_identity_mismatches_are_rejected(mutator, message):
    receipt = _receipt()
    mutator(receipt)
    if message != "receipt_id does not match":
        _rehash(receipt)
    with pytest.raises(ValueError, match=message):
        publication_receipts.validate_publication_receipt(receipt, current=_current())


def test_unknown_article_and_non_importable_status_are_rejected(monkeypatch):
    monkeypatch.setattr(publication_receipts, "get_article_record", lambda article_id: None)
    with pytest.raises(ValueError, match="unknown to registry"):
        publication_receipts.import_publication_receipt(_receipt(), record=False)

    with pytest.raises(ValueError, match="status cannot accept"):
        publication_receipts.validate_publication_receipt(_receipt(), current=_current("rejected_for_revision"))


def test_conflicting_second_publication_receipt_is_rejected():
    first = _receipt(321)
    current = {
        **_current("published"),
        "cms_id": 321,
        "published_url": first["published_url"],
        "publication_receipt_id": first["receipt_id"],
    }
    second = _receipt(322)
    with pytest.raises(ValueError, match="URL conflicts|cms_id conflicts|receipt_id conflicts"):
        publication_receipts.validate_publication_receipt(second, current=current)
