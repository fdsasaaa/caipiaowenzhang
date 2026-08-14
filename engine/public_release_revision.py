from __future__ import annotations

import json
import os
from pathlib import Path

from .formal_approved_inventory import FormalInventoryError, validate_formal_approved_package
from .store import ROOT
from .text import sha256_text

REVISION_KIND = "website_public_release"
RELEASE_ROOT = ROOT / "articles" / "public_release"
MANIFEST_ROOT = RELEASE_ROOT / "manifests"


class PublicReleaseRevisionError(ValueError):
    pass


def _canonical_json(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _portable_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def expected_public_release_fingerprint(package: dict) -> str:
    identity = {
        "article_id": str(package.get("article_id") or ""),
        "revision_id": str(package.get("revision_id") or ""),
        "revision_kind": str(package.get("revision_kind") or ""),
        "release_revision": int(package.get("release_revision") or 0),
        "parent_content_hash": str(package.get("parent_content_hash") or ""),
        "parent_fingerprint": str(package.get("parent_fingerprint") or ""),
        "content_hash": str(package.get("content_hash") or ""),
        "slug": str(package.get("slug") or ""),
        "primary_keyword": str(package.get("primary_keyword") or ""),
    }
    return sha256_text(_canonical_json(identity))


def _load_parent(article_id: str, approved_root: Path) -> dict:
    parent_path = approved_root / f"{article_id}.json"
    if not parent_path.is_file():
        raise PublicReleaseRevisionError(f"parent Approved Package not found: {parent_path.name}")
    try:
        parent = json.loads(parent_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PublicReleaseRevisionError(f"parent Approved Package is invalid: {parent_path.name}") from exc
    if not isinstance(parent, dict):
        raise PublicReleaseRevisionError("parent Approved Package must be a JSON object")
    try:
        validate_formal_approved_package(parent)
    except FormalInventoryError as exc:
        raise PublicReleaseRevisionError(f"parent Approved Package failed formal validation: {exc}") from exc
    return parent


def validate_public_release_revision(
    package: dict,
    *,
    approved_root: Path | None = None,
) -> dict:
    if not isinstance(package, dict):
        raise PublicReleaseRevisionError("public-release revision must be a JSON object")

    try:
        validate_formal_approved_package(package)
    except FormalInventoryError as exc:
        raise PublicReleaseRevisionError(f"revision failed Formal Approved validation: {exc}") from exc

    article_id = str(package.get("article_id") or "").strip()
    release_revision = package.get("release_revision")
    if not isinstance(release_revision, int) or isinstance(release_revision, bool) or release_revision < 1:
        raise PublicReleaseRevisionError("release_revision must be a positive integer")
    if package.get("revision_kind") != REVISION_KIND:
        raise PublicReleaseRevisionError(f"revision_kind must be {REVISION_KIND}")
    expected_revision_id = f"{article_id}:public-r{release_revision}"
    if str(package.get("revision_id") or "") != expected_revision_id:
        raise PublicReleaseRevisionError(f"revision_id must be {expected_revision_id}")

    approved_root = approved_root or (ROOT / "articles" / "approved")
    parent = _load_parent(article_id, approved_root)
    parent_hash = str(parent.get("content_hash") or "").strip().lower()
    parent_fingerprint = str(parent.get("fingerprint") or "").strip()

    if str(package.get("parent_content_hash") or "").strip().lower() != parent_hash:
        raise PublicReleaseRevisionError("parent_content_hash does not match immutable Approved parent")
    if str(package.get("parent_fingerprint") or "").strip() != parent_fingerprint:
        raise PublicReleaseRevisionError("parent_fingerprint does not match immutable Approved parent")
    if str(package.get("content_hash") or "").strip().lower() == parent_hash:
        raise PublicReleaseRevisionError("public-release revision must change content and content_hash")

    for field in ("slug", "primary_keyword", "site_category_key", "content_type"):
        if package.get(field) != parent.get(field):
            raise PublicReleaseRevisionError(f"public-release revision must preserve parent {field}")

    source_batch_id = str(package.get("source_batch_id") or "").strip()
    parent_batch_id = str(parent.get("creator_batch_id") or "").strip()
    if not source_batch_id or source_batch_id != parent_batch_id:
        raise PublicReleaseRevisionError("source_batch_id must match parent creator_batch_id")

    review = package.get("public_release_review")
    if not isinstance(review, dict) or review.get("status") != "approved":
        raise PublicReleaseRevisionError("public_release_review.status must be approved")
    if not str(review.get("reviewed_at") or "").strip():
        raise PublicReleaseRevisionError("public_release_review.reviewed_at is required")
    if not str(review.get("review_contract") or "").strip():
        raise PublicReleaseRevisionError("public_release_review.review_contract is required")

    expected_fingerprint = expected_public_release_fingerprint(package)
    if str(package.get("fingerprint") or "") != expected_fingerprint:
        raise PublicReleaseRevisionError("fingerprint does not match public-release revision identity")

    return {
        "article_id": article_id,
        "revision_id": expected_revision_id,
        "release_revision": release_revision,
        "source_batch_id": source_batch_id,
        "content_hash": str(package["content_hash"]),
        "fingerprint": expected_fingerprint,
    }


def stage_public_release_revision(
    package: dict,
    *,
    approved_root: Path | None = None,
    release_root: Path | None = None,
) -> dict:
    validated = validate_public_release_revision(package, approved_root=approved_root)
    release_root = release_root or RELEASE_ROOT
    batch_dir = release_root / validated["source_batch_id"]
    batch_dir.mkdir(parents=True, exist_ok=True)
    target = batch_dir / f"{validated['article_id']}.public-r{validated['release_revision']}.json"
    canonical = _canonical_json(package)

    if target.exists():
        try:
            existing = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PublicReleaseRevisionError(f"existing public-release revision is invalid: {target.name}") from exc
        if isinstance(existing, dict) and _canonical_json(existing) == canonical:
            return {"status": "unchanged", "path": _portable_path(target), **validated}
        raise PublicReleaseRevisionError("public-release revision path already exists with different content")

    encoded = json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp = target.with_name(target.name + f".tmp.{os.getpid()}")
    try:
        tmp.write_text(encoded, encoding="utf-8", newline="\n")
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
    return {"status": "staged", "path": _portable_path(target), **validated}


def build_public_release_manifest(
    source_batch_id: str,
    *,
    expected_count: int,
    approved_root: Path | None = None,
    release_root: Path | None = None,
) -> dict:
    if expected_count < 1:
        raise PublicReleaseRevisionError("expected_count must be positive")
    approved_root = approved_root or (ROOT / "articles" / "approved")
    release_root = release_root or RELEASE_ROOT
    batch_dir = release_root / source_batch_id
    paths = sorted(batch_dir.glob("*.public-r*.json")) if batch_dir.is_dir() else []

    latest: dict[str, tuple[int, dict, Path]] = {}
    for path in paths:
        try:
            package = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PublicReleaseRevisionError(f"invalid public-release file: {path.name}") from exc
        validated = validate_public_release_revision(package, approved_root=approved_root)
        if validated["source_batch_id"] != source_batch_id:
            raise PublicReleaseRevisionError(f"batch mismatch in {path.name}")
        article_id = validated["article_id"]
        revision = validated["release_revision"]
        previous = latest.get(article_id)
        if previous is None or revision > previous[0]:
            latest[article_id] = (revision, package, path)

    articles = []
    for article_id in sorted(latest):
        revision, package, path = latest[article_id]
        articles.append(
            {
                "article_id": article_id,
                "revision_id": package["revision_id"],
                "release_revision": revision,
                "slug": package["slug"],
                "primary_keyword": package["primary_keyword"],
                "content_hash": package["content_hash"],
                "fingerprint": package["fingerprint"],
                "path": _portable_path(path),
            }
        )

    count = len(articles)
    return {
        "schema_version": 1,
        "source_batch_id": source_batch_id,
        "revision_kind": REVISION_KIND,
        "expected_count": expected_count,
        "approved_public_release_count": count,
        "status": "complete" if count == expected_count else "partial",
        "website_batch_ingestion_allowed": count == expected_count,
        "canary_ingestion_allowed": count > 0,
        "articles": articles,
    }


def write_public_release_manifest(
    source_batch_id: str,
    *,
    expected_count: int,
    approved_root: Path | None = None,
    release_root: Path | None = None,
    manifest_root: Path | None = None,
) -> dict:
    manifest = build_public_release_manifest(
        source_batch_id,
        expected_count=expected_count,
        approved_root=approved_root,
        release_root=release_root,
    )
    manifest_root = manifest_root or MANIFEST_ROOT
    manifest_root.mkdir(parents=True, exist_ok=True)
    target = manifest_root / f"{source_batch_id}.json"
    encoded = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp = target.with_name(target.name + f".tmp.{os.getpid()}")
    try:
        tmp.write_text(encoded, encoding="utf-8", newline="\n")
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
    return {"status": "manifest_written", "path": _portable_path(target), **manifest}
