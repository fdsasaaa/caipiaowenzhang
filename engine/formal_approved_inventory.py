from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .site_contract import normalize_seo_cluster_assignment, site_category_for
from .store import ROOT
from .text import sha256_text
from .title_seo import validate_title_contract_fields

ARTICLE_ID_RE = re.compile(r"^[A-Za-z0-9._:-]+$")


class FormalInventoryError(ValueError):
    pass


def _canonical_json(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def validate_formal_approved_package(package: dict) -> None:
    if not isinstance(package, dict):
        raise FormalInventoryError("Approved Package must be a JSON object")
    if package.get("status") != "approved":
        raise FormalInventoryError("status must be approved")

    article_id = str(package.get("article_id") or "").strip()
    if not article_id or ARTICLE_ID_RE.fullmatch(article_id) is None:
        raise FormalInventoryError("article_id missing or contains unsupported characters")

    content = package.get("content")
    if not isinstance(content, str) or not content.strip():
        raise FormalInventoryError("content must be a non-empty string")
    content_hash = str(package.get("content_hash") or "").strip().lower()
    if not content_hash:
        raise FormalInventoryError("content_hash is required for formal inventory")
    if content_hash != sha256_text(content):
        raise FormalInventoryError("content_hash does not match content")

    fingerprint = str(package.get("fingerprint") or "").strip()
    if not fingerprint:
        raise FormalInventoryError("fingerprint is required for formal inventory")

    content_type = str(package.get("content_type") or "").strip()
    if not content_type:
        raise FormalInventoryError("content_type is required for formal inventory")
    try:
        expected_category = site_category_for(content_type)
    except (LookupError, ValueError) as exc:
        raise FormalInventoryError(str(exc)) from exc
    actual_category = str(package.get("site_category_key") or "").strip()
    if actual_category != expected_category:
        raise FormalInventoryError(
            f"site_category_key mismatch for content_type {content_type}: expected {expected_category}, got {actual_category or '<empty>'}"
        )

    try:
        primary, secondary = normalize_seo_cluster_assignment(
            package.get("primary_seo_cluster_id"),
            package.get("secondary_seo_cluster_ids"),
        )
    except ValueError as exc:
        raise FormalInventoryError(str(exc)) from exc
    if (primary is not None or secondary) and actual_category != "tzjq":
        raise FormalInventoryError("SEO cluster metadata is only allowed for tzjq articles")

    # Legacy Approved parents remain valid and immutable. Every new package carrying
    # Title SEO V1.0 metadata must prove that the complete title contract passed.
    if package.get("title_seo_contract_version"):
        title_errors = validate_title_contract_fields(package)
        if title_errors:
            raise FormalInventoryError("Title SEO contract invalid: " + "; ".join(title_errors))
        if (package.get("title_review") or {}).get("passed") is not True:
            raise FormalInventoryError("Title SEO review must pass before formal inventory")


def stage_formal_approved_package(package: dict, approved_root: Path | None = None) -> dict:
    validate_formal_approved_package(package)
    approved_root = approved_root or (ROOT / "articles" / "approved")
    approved_root.mkdir(parents=True, exist_ok=True)

    article_id = str(package["article_id"]).strip()
    target = approved_root / f"{article_id}.json"
    canonical = _canonical_json(package)

    if target.exists():
        try:
            existing = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise FormalInventoryError(f"existing formal inventory file is invalid: {target.name}") from exc
        if not isinstance(existing, dict):
            raise FormalInventoryError(f"existing formal inventory file is not a JSON object: {target.name}")
        if _canonical_json(existing) == canonical:
            return {"status": "unchanged", "article_id": article_id, "path": str(target)}

        existing_hash = str(existing.get("content_hash") or "").strip().lower()
        incoming_hash = str(package.get("content_hash") or "").strip().lower()
        if existing_hash != incoming_hash:
            raise FormalInventoryError(
                "formal inventory already contains this article_id with a different content_hash; revision + re-Approval path required"
            )
        raise FormalInventoryError(
            "formal inventory already contains this article_id with different approved metadata; explicit approved-inventory revision path required"
        )

    encoded = json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp = target.with_name(target.name + f".tmp.{os.getpid()}")
    try:
        tmp.write_text(encoded, encoding="utf-8", newline="\n")
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)

    return {"status": "staged", "article_id": article_id, "path": str(target)}


def stage_formal_approved_file(input_path: Path, approved_root: Path | None = None) -> dict:
    try:
        package = json.loads(input_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FormalInventoryError(f"cannot read Approved Package: {input_path}") from exc
    if not isinstance(package, dict):
        raise FormalInventoryError("Approved Package file must contain a JSON object")
    return stage_formal_approved_package(package, approved_root=approved_root)
