from __future__ import annotations

import json
from pathlib import Path

from engine.creator_first import build_creator_request, validate_creator_output
from engine.dedup import LEXICAL_DUPLICATE_THRESHOLD, lexical_similarity
from engine.formal_approved_inventory import validate_formal_approved_package
from engine.semantic_dedup import STRUCTURAL_DUPLICATE_THRESHOLD, structural_similarity

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "agent" / "results" / "CREATOR_FIRST_BATCH_50_PAYLOADS_2026-08-13.jsonl"
APPROVED = ROOT / "articles" / "approved"


def _rows():
    return [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line.strip()]


def _package(article_id: str):
    return json.loads((APPROVED / f"{article_id}.json").read_text(encoding="utf-8"))


def test_creator_first_batch_50_all_pass_existing_approval_and_formal_inventory():
    rows = _rows()
    assert len(rows) == 50

    for row in rows:
        request = build_creator_request(request_id=row["request_id"])
        result = validate_creator_output(
            request,
            {"manifest": row["manifest"], "article": row["article"]},
        )
        assert result.approved, f"{row['request_id']}: {result.errors}"

        package = _package(result.article["article_id"])
        validate_formal_approved_package(package)

        generated = result.approval.publish_package
        assert generated is not None
        for field in (
            "article_id", "title", "seo_title", "slug", "meta_description",
            "primary_keyword", "search_intent", "summary", "category",
            "site_category_key", "content_type", "content_format", "content",
            "rule_refs", "source_refs", "case_scope", "lottery", "play",
            "subject_lottery", "subject_play", "technique_atoms", "fingerprint",
            "content_hash", "status", "generation_contract_version", "claim_evidence",
        ):
            assert package.get(field) == generated.get(field), (
                row["request_id"], field, package.get(field), generated.get(field)
            )


def test_creator_first_batch_50_has_unique_seo_identity_and_no_intra_batch_duplicates():
    rows = _rows()
    packages = [_package(row["article"]["article_id"]) for row in rows]

    assert len({row["article_id"] for row in packages}) == 50
    assert len({row["slug"] for row in packages}) == 50
    assert len({row["primary_keyword"] for row in packages}) == 50
    assert len({row["content_hash"] for row in packages}) == 50

    conflicts = []
    for i, left in enumerate(packages):
        for right in packages[i + 1:]:
            lexical = lexical_similarity(left, right)
            structural = structural_similarity(left, right)
            if lexical >= LEXICAL_DUPLICATE_THRESHOLD or structural >= STRUCTURAL_DUPLICATE_THRESHOLD:
                conflicts.append({
                    "left": left["article_id"],
                    "right": right["article_id"],
                    "lexical": lexical,
                    "structural": structural,
                })
    assert not conflicts, conflicts[:10]


def test_creator_first_batch_50_remains_inventory_only():
    for row in _rows():
        package = _package(row["article"]["article_id"])
        assert package.get("status") == "approved"
        assert package.get("published_url") in (None, "")
        assert package.get("published_at") in (None, "")
