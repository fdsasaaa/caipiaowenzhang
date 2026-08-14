from __future__ import annotations

import json
from pathlib import Path

from engine.creative_memory import (
    build_long_term_memory_snapshot,
    formal_inventory_duplicate_hits,
    formal_inventory_records,
    select_style_dna,
)
from engine.creator_quality import build_quality_creator_request

ROOT = Path(__file__).resolve().parents[1]
APPROVED = ROOT / "articles" / "approved"


def test_style_dna_is_deterministic_soft_guidance():
    left = select_style_dna("same-request")
    right = select_style_dna("same-request")
    assert left == right
    assert left["id"]
    assert left["voice"]
    assert left["opening"]
    assert left["bias"]


def test_long_term_memory_reads_formal_inventory_not_only_registry():
    formal_files = sorted(APPROVED.glob("*.json"))
    assert len(formal_files) >= 50
    records = formal_inventory_records()
    ids = {str(row.get("article_id") or "") for row in records}
    assert "LCM-CREATOR-cf50-20260813-001" in ids

    snapshot = build_long_term_memory_snapshot(representative_limit=24, coverage_limit=40)
    assert snapshot["article_count"] >= 50
    assert len(snapshot["representative_articles"]) <= 24
    assert len(snapshot["coverage_signatures"]) <= 40
    assert snapshot["memory_role"].startswith("avoid substantive repetition")


def test_formal_inventory_long_term_duplicate_gate_sees_existing_approved_article():
    source_path = APPROVED / "LCM-CREATOR-cf50-20260813-001.json"
    source = json.loads(source_path.read_text(encoding="utf-8"))
    candidate = dict(source)
    candidate["article_id"] = "LCM-CREATOR-test-duplicate-memory"
    hits = formal_inventory_duplicate_hits(candidate)
    assert hits
    assert hits[0]["article_id"] == source["article_id"]
    assert any(
        reason in {"same_primary_keyword", "same_slug", "same_content_hash"}
        or reason.startswith("lexical=")
        for reason in hits[0]["reasons"]
    )


def test_quality_request_adds_memory_style_and_title_choice_without_changing_safety_flags():
    request = build_quality_creator_request(request_id="quality-memory-smoke")
    assert request["style_dna"]["id"]
    assert request["long_term_memory"]["article_count"] >= 50
    assert request["title_selection"]["internal_candidate_count"] == 5
    assert request["title_selection"]["output_only_final_winner"] is True
    assert request["automatic_retry"] is False
    assert request["website_sync"] is False
    assert request["scheduled"] is False
    assert request["published"] is False
    assert any("仅仅更换参数不算创新" in item for item in request["creative_mandate"])
