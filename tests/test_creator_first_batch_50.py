from __future__ import annotations

import json
from pathlib import Path

from engine.creator_first import build_creator_request, validate_creator_output
from engine.dedup import LEXICAL_DUPLICATE_THRESHOLD, lexical_similarity
from engine.formal_approved_inventory import validate_formal_approved_package
from engine.semantic_dedup import STRUCTURAL_DUPLICATE_THRESHOLD, structural_similarity

ROOT = Path(__file__).resolve().parents[1]
APPROVED = ROOT / "articles" / "approved"
PATTERN = "LCM-CREATOR-cf50-20260813-*.json"
CASE_LABEL = "演示参数，不是真实开奖记录"


def _packages() -> list[dict]:
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(APPROVED.glob(PATTERN))
    ]


def _creator_payload(package: dict) -> tuple[dict, dict]:
    article_id = str(package["article_id"])
    request_id = article_id.removeprefix("LCM-CREATOR-")
    request = build_creator_request(request_id=request_id)
    rule_refs = list(package.get("rule_refs") or [])
    assert len(rule_refs) == 1
    tags = list(package.get("technique_atoms") or ["creator_original"])
    manifest = {
        "selected_rule_ref": rule_refs[0],
        "subject_lottery": package["subject_lottery"],
        "subject_play": package["subject_play"],
        "creation_mode": "hybrid",
        "technique_name": package["primary_keyword"],
        "technique_tags": tags,
        "originality_note": "Creator-first original batch article; existing inventory is memory, not template.",
        "reader_value": "Explain one reproducible technique clearly, including boundaries and stopping discipline.",
        "uses_draw_data": False,
        "uses_bankroll_design": True,
        "uses_staking_design": any("staking" in x or "bankroll" in x for x in tags),
        "bankroll_design_summary": "Uses relative units only; no unverified provider economics.",
        "staking_design_summary": "Research-only bounded staking when present; no profit guarantee.",
        "case_label": CASE_LABEL,
        "case_notes": [],
    }
    article = dict(package)
    article["status"] = "draft"
    for field in (
        "approved_at", "content_hash", "fingerprint", "creator_batch_id",
        "creator_first_contract_version", "published_url", "published_at",
    ):
        article.pop(field, None)
    return request, {"manifest": manifest, "article": article}


def test_creator_first_batch_50_all_pass_existing_approval_and_formal_inventory():
    packages = _packages()
    assert len(packages) == 50
    failures = []

    for package in packages:
        validate_formal_approved_package(package)
        request, payload = _creator_payload(package)
        result = validate_creator_output(request, payload)
        if not result.approved:
            failures.append({"article_id": package["article_id"], "errors": result.errors})
            continue

        generated = result.approval.publish_package
        assert generated is not None
        for field in (
            "article_id", "title", "seo_title", "slug", "meta_description",
            "primary_keyword", "search_intent", "summary", "category",
            "site_category_key", "content_type", "content_format", "content",
            "rule_refs", "source_refs", "case_scope", "lottery", "play",
            "subject_lottery", "subject_play", "technique_atoms",
            "content_hash", "status", "generation_contract_version", "claim_evidence",
        ):
            assert package.get(field) == generated.get(field), (
                package["article_id"], field, package.get(field), generated.get(field)
            )

    assert not failures, failures


def test_creator_first_batch_50_has_unique_seo_identity_and_no_intra_batch_duplicates():
    packages = _packages()
    assert len(packages) == 50
    assert len({row["article_id"] for row in packages}) == 50
    assert len({row["slug"] for row in packages}) == 50
    assert len({row["primary_keyword"] for row in packages}) == 50
    assert len({row["content_hash"] for row in packages}) == 50

    conflicts = []
    for i, left in enumerate(packages):
        for right in packages[i + 1:]:
            lexical = lexical_similarity(left, right)
            structural, reasons = structural_similarity(left, right)
            if lexical >= LEXICAL_DUPLICATE_THRESHOLD or structural >= STRUCTURAL_DUPLICATE_THRESHOLD:
                conflicts.append({
                    "left": left["article_id"],
                    "right": right["article_id"],
                    "lexical": lexical,
                    "structural": structural,
                    "reasons": reasons,
                })
    assert not conflicts, conflicts[:10]


def test_creator_first_batch_50_remains_inventory_only():
    for package in _packages():
        assert package.get("status") == "approved"
        assert package.get("published_url") in (None, "")
        assert package.get("published_at") in (None, "")
