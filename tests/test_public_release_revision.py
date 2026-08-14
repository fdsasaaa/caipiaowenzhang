from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.public_release_revision import (
    PublicReleaseRevisionError,
    build_public_release_manifest,
    expected_public_release_fingerprint,
    stage_public_release_revision,
)
from engine.text import sha256_text


def _parent() -> dict:
    content = "<p>General educational source document used only for revision-contract tests.</p>" * 5
    return {
        "status": "approved",
        "article_id": "TEST-PUBLIC-001",
        "content": content,
        "content_hash": sha256_text(content),
        "fingerprint": "parent-fingerprint-001",
        "content_type": "technique_article",
        "site_category_key": "tzjq",
        "slug": "test-public-001",
        "primary_keyword": "test public keyword",
        "creator_batch_id": "TEST-BATCH-001",
    }


def _write_parent(root: Path, parent: dict) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / f"{parent['article_id']}.json").write_text(
        json.dumps(parent, ensure_ascii=False), encoding="utf-8"
    )


def _revision(parent: dict) -> dict:
    content = parent["content"] + "<p>Reviewed website-facing revision.</p>"
    revision = dict(parent)
    revision.update(
        {
            "content": content,
            "content_hash": sha256_text(content),
            "revision_kind": "website_public_release",
            "release_revision": 1,
            "revision_id": f"{parent['article_id']}:public-r1",
            "parent_content_hash": parent["content_hash"],
            "parent_fingerprint": parent["fingerprint"],
            "source_batch_id": parent["creator_batch_id"],
            "public_release_review": {
                "status": "approved",
                "reviewed_at": "2026-08-14T00:00:00Z",
                "review_contract": "website-public-release-v1",
            },
        }
    )
    revision["fingerprint"] = expected_public_release_fingerprint(revision)
    return revision


def test_stage_and_partial_manifest_allow_canary(tmp_path: Path) -> None:
    approved_root = tmp_path / "approved"
    release_root = tmp_path / "public_release"
    parent = _parent()
    _write_parent(approved_root, parent)
    revision = _revision(parent)

    result = stage_public_release_revision(
        revision, approved_root=approved_root, release_root=release_root
    )
    assert result["status"] == "staged"
    assert result["article_id"] == parent["article_id"]

    manifest = build_public_release_manifest(
        parent["creator_batch_id"],
        expected_count=2,
        approved_root=approved_root,
        release_root=release_root,
    )
    assert manifest["status"] == "partial"
    assert manifest["approved_public_release_count"] == 1
    assert manifest["canary_ingestion_allowed"] is True
    assert manifest["website_batch_ingestion_allowed"] is False


def test_revision_rejects_parent_hash_mismatch(tmp_path: Path) -> None:
    approved_root = tmp_path / "approved"
    parent = _parent()
    _write_parent(approved_root, parent)
    revision = _revision(parent)
    revision["parent_content_hash"] = "0" * 64
    revision["fingerprint"] = expected_public_release_fingerprint(revision)

    with pytest.raises(PublicReleaseRevisionError, match="parent_content_hash"):
        stage_public_release_revision(revision, approved_root=approved_root, release_root=tmp_path / "release")


def test_revision_rejects_unchanged_content(tmp_path: Path) -> None:
    approved_root = tmp_path / "approved"
    parent = _parent()
    _write_parent(approved_root, parent)
    revision = _revision(parent)
    revision["content"] = parent["content"]
    revision["content_hash"] = parent["content_hash"]
    revision["fingerprint"] = expected_public_release_fingerprint(revision)

    with pytest.raises(PublicReleaseRevisionError, match="must change content"):
        stage_public_release_revision(revision, approved_root=approved_root, release_root=tmp_path / "release")


def test_revision_rejects_unapproved_public_review(tmp_path: Path) -> None:
    approved_root = tmp_path / "approved"
    parent = _parent()
    _write_parent(approved_root, parent)
    revision = _revision(parent)
    revision["public_release_review"]["status"] = "pending"

    with pytest.raises(PublicReleaseRevisionError, match="public_release_review.status"):
        stage_public_release_revision(revision, approved_root=approved_root, release_root=tmp_path / "release")
