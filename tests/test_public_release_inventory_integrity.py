from __future__ import annotations

import json
from pathlib import Path

from engine.public_release_revision import (
    MANIFEST_ROOT,
    RELEASE_ROOT,
    build_public_release_manifest,
    validate_public_release_revision,
)
from engine.store import ROOT


def test_every_public_release_revision_and_manifest_is_self_consistent() -> None:
    approved_root = ROOT / "articles" / "approved"
    manifest_paths = sorted(MANIFEST_ROOT.glob("*.json")) if MANIFEST_ROOT.is_dir() else []
    batches = sorted(path for path in RELEASE_ROOT.iterdir() if path.is_dir() and path.name != "manifests")

    manifest_by_batch: dict[str, Path] = {path.stem: path for path in manifest_paths}
    assert batches, "expected at least one public-release batch"

    for batch_dir in batches:
        source_batch_id = batch_dir.name
        assert source_batch_id in manifest_by_batch, f"missing public-release manifest for {source_batch_id}"
        revision_paths = sorted(batch_dir.glob("*.public-r*.json"))
        assert revision_paths, f"public-release batch {source_batch_id} is empty"

        seen_revision_ids: set[str] = set()
        for revision_path in revision_paths:
            package = json.loads(revision_path.read_text(encoding="utf-8"))
            validated = validate_public_release_revision(package, approved_root=approved_root)
            assert validated["source_batch_id"] == source_batch_id
            assert validated["revision_id"] not in seen_revision_ids, (
                f"duplicate revision_id {validated['revision_id']} in {source_batch_id}"
            )
            seen_revision_ids.add(validated["revision_id"])

        stored_manifest = json.loads(
            manifest_by_batch[source_batch_id].read_text(encoding="utf-8")
        )
        expected_count = stored_manifest.get("expected_count")
        assert isinstance(expected_count, int) and not isinstance(expected_count, bool) and expected_count > 0
        regenerated = build_public_release_manifest(
            source_batch_id,
            expected_count=expected_count,
            approved_root=approved_root,
            release_root=RELEASE_ROOT,
        )
        assert stored_manifest == regenerated, (
            f"public-release manifest drift for {source_batch_id}; regenerate it from validated revisions"
        )


def test_no_orphan_public_release_manifest_exists() -> None:
    batch_ids = {
        path.name
        for path in RELEASE_ROOT.iterdir()
        if path.is_dir() and path.name != "manifests"
    }
    manifest_ids = {path.stem for path in MANIFEST_ROOT.glob("*.json")}
    assert manifest_ids <= batch_ids, f"orphan public-release manifests: {sorted(manifest_ids - batch_ids)}"
