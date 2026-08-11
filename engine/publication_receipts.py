from __future__ import annotations

import re
from datetime import datetime
from pathlib import PurePosixPath

from .article_memory import append_article_state, get_article_record
from .site_urls import validate_published_url
from .text import sha256_text

HEX64 = re.compile(r"^[a-f0-9]{64}$")
IMPORTABLE_STATUSES = {"approved", "queued", "scheduled", "published"}


def publication_receipt_id(receipt: dict) -> str:
    parts = [
        "v1",
        str(receipt.get("article_id") or ""),
        str(receipt.get("article_key") or ""),
        str(receipt.get("fingerprint") or ""),
        str(receipt.get("content_hash") or ""),
        str(receipt.get("cms_id") or ""),
        str(receipt.get("published_url") or ""),
        str(receipt.get("published_at") or ""),
        str(receipt.get("publisher_article_hash") or ""),
        str(receipt.get("source_file") or ""),
    ]
    return sha256_text("|".join(parts))


def _validated_timestamp(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("publication receipt missing published_at")
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("publication receipt has invalid published_at") from exc
    if parsed.tzinfo is None:
        raise ValueError("publication receipt published_at must include timezone")
    return raw


def validate_publication_receipt(receipt: dict, current: dict | None = None) -> dict:
    if not isinstance(receipt, dict):
        raise ValueError("publication receipt must be an object")
    if receipt.get("schema_version") != 1:
        raise ValueError("unsupported publication receipt schema_version")
    if receipt.get("receipt_type") != "publication_receipt":
        raise ValueError("invalid publication receipt_type")

    article_id = str(receipt.get("article_id") or "").strip()
    article_key = str(receipt.get("article_key") or "").strip()
    fingerprint = str(receipt.get("fingerprint") or "").strip().lower()
    content_hash = str(receipt.get("content_hash") or "").strip().lower()
    publisher_hash = str(receipt.get("publisher_article_hash") or "").strip().lower()
    source_file = str(receipt.get("source_file") or "").strip()
    receipt_id = str(receipt.get("receipt_id") or "").strip().lower()
    site_base_url = str(receipt.get("site_base_url") or "").strip().rstrip("/")

    if not article_id:
        raise ValueError("publication receipt missing article_id")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{2,79}", article_key):
        raise ValueError("publication receipt has invalid article_key")
    if not HEX64.fullmatch(fingerprint):
        raise ValueError("publication receipt has invalid fingerprint")
    if not HEX64.fullmatch(content_hash):
        raise ValueError("publication receipt has invalid content_hash")
    if not HEX64.fullmatch(publisher_hash):
        raise ValueError("publication receipt has invalid publisher_article_hash")
    if source_file != article_key + ".json":
        raise ValueError("publication receipt source_file does not match article_key")
    if site_base_url not in {"https://laocaimi.org", "https://www.laocaimi.org"}:
        raise ValueError("publication receipt has invalid site_base_url")

    cms_id = receipt.get("cms_id")
    if isinstance(cms_id, bool) or not isinstance(cms_id, int) or cms_id <= 0:
        raise ValueError("publication receipt has invalid cms_id")
    published_url = validate_published_url(str(receipt.get("published_url") or ""))
    expected_url = f"{site_base_url}/index.php?c=show&id={cms_id}"
    if published_url != expected_url:
        raise ValueError("publication receipt published_url does not match cms_id/site_base_url")
    published_at = _validated_timestamp(receipt.get("published_at"))

    expected_receipt_id = publication_receipt_id(receipt)
    if not HEX64.fullmatch(receipt_id) or receipt_id != expected_receipt_id:
        raise ValueError("publication receipt_id does not match immutable receipt fields")

    current = current if current is not None else get_article_record(article_id)
    if not current:
        raise ValueError("publication receipt article_id is unknown to registry")
    if current.get("status") not in IMPORTABLE_STATUSES:
        raise ValueError("registry article status cannot accept publication receipt: " + str(current.get("status")))
    if str(current.get("fingerprint") or "").lower() != fingerprint:
        raise ValueError("publication receipt fingerprint does not match registry")
    if str(current.get("content_hash") or "").lower() != content_hash:
        raise ValueError("publication receipt content_hash does not match registry")

    draft_path = str(current.get("website_draft_path") or "").strip()
    if not draft_path:
        raise ValueError("registry article is missing website_draft_path provenance")
    if PurePosixPath(draft_path).stem != article_key:
        raise ValueError("publication receipt article_key does not match website_draft_path")

    if current.get("status") == "published":
        old_url = str(current.get("published_url") or "")
        old_cms_id = current.get("cms_id")
        old_receipt = str(current.get("publication_receipt_id") or "")
        if old_url and old_url != published_url:
            raise ValueError("published registry URL conflicts with publication receipt")
        if old_cms_id is not None and int(old_cms_id) != cms_id:
            raise ValueError("published registry cms_id conflicts with publication receipt")
        if old_receipt and old_receipt != receipt_id:
            raise ValueError("published registry receipt_id conflicts with publication receipt")

    return {
        "article_id": article_id,
        "article_key": article_key,
        "fingerprint": fingerprint,
        "content_hash": content_hash,
        "cms_id": cms_id,
        "published_url": published_url,
        "published_at": published_at,
        "publisher_article_hash": publisher_hash,
        "publication_receipt_id": receipt_id,
        "website_published_source_file": source_file,
        "site_base_url": site_base_url,
    }


def import_publication_receipt(receipt: dict, record: bool = False) -> dict:
    article_id = str(receipt.get("article_id") or "").strip()
    current = get_article_record(article_id) if article_id else None
    validated = validate_publication_receipt(receipt, current=current)

    if current and current.get("status") == "published":
        if (
            str(current.get("published_url") or "") == validated["published_url"]
            and int(current.get("cms_id") or 0) == validated["cms_id"]
            and str(current.get("publication_receipt_id") or "") == validated["publication_receipt_id"]
        ):
            return {"status": "unchanged", "recorded": False, **validated}

    changes = {
        "cms_id": validated["cms_id"],
        "published_url": validated["published_url"],
        "published_at": validated["published_at"],
        "publisher_article_hash": validated["publisher_article_hash"],
        "publication_receipt_id": validated["publication_receipt_id"],
        "website_published_source_file": validated["website_published_source_file"],
    }
    if not record:
        preview = dict(current or {})
        preview.update(changes)
        preview["article_id"] = validated["article_id"]
        preview["status"] = "published"
        return {"status": "validated", "recorded": False, "registry_record": preview, **validated}

    registry_record = append_article_state(validated["article_id"], "published", changes)
    return {"status": "recorded", "recorded": True, "registry_record": registry_record, **validated}
