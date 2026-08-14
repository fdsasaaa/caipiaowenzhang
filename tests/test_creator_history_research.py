from __future__ import annotations

from copy import deepcopy

from engine.creator_history_research import build_history_research_creator_request
from engine.draw_research import (
    build_draw_research_context,
    records_sha256,
    validate_draw_dataset,
)


def _dataset(count: int = 60) -> dict:
    records = []
    for index in range(count):
        records.append({
            "issue": f"20260814-{index + 1:04d}",
            "digits": [
                index % 10,
                (index * 3 + 1) % 10,
                (index * 7 + 2) % 10,
                (index * 5 + 3) % 10,
                (index * 9 + 4) % 10,
            ],
        })
    return {
        "schema_version": "1.0",
        "dataset_id": "TEST-SSC-HISTORY-60",
        "lottery": "时时彩",
        "positions": ["万", "千", "百", "十", "个"],
        "provenance": {
            "verification_status": "verified_external",
            "source_note": "test fixture only",
            "collected_at": "2026-08-14T00:00:00Z",
            "records_sha256": records_sha256(records),
        },
        "records": records,
    }


def test_draw_dataset_contract_accepts_verified_normalized_history():
    dataset = _dataset()
    report = validate_draw_dataset(dataset)
    assert report.passed
    assert report.record_count == 60
    assert report.dataset_hash == dataset["provenance"]["records_sha256"]

    context = build_draw_research_context(dataset, recent_limit=10, sample_limit=12)
    assert context["record_count"] == 60
    assert len(context["recent_records"]) == 10
    assert len(context["stratified_sample"]) <= 12
    assert context["research_role"].startswith("private hypothesis")
    assert "后二绝对差分布" in context["relationship_summary"]


def test_draw_dataset_contract_rejects_unverified_or_mutated_history():
    unverified = _dataset()
    unverified["provenance"]["verification_status"] = "unverified"
    assert not validate_draw_dataset(unverified).passed

    mutated = _dataset()
    mutated["records"][0]["digits"][0] = 9
    report = validate_draw_dataset(mutated)
    assert not report.passed
    assert any("sha256" in error for error in report.errors)

    duplicate = deepcopy(_dataset())
    duplicate["records"][1]["issue"] = duplicate["records"][0]["issue"]
    duplicate["provenance"]["records_sha256"] = records_sha256(duplicate["records"])
    report = validate_draw_dataset(duplicate)
    assert not report.passed
    assert any("duplicate issue" in error for error in report.errors)


def test_history_research_request_is_additive_and_keeps_v11_safety():
    request = build_history_research_creator_request(_dataset(), request_id="history-v12-smoke")
    assert request["draw_data_available"] is True
    assert request["draw_research_mode"] == "idea_only_v1.2"
    assert request["draw_research_context"]["dataset_id"] == "TEST-SSC-HISTORY-60"

    # V1.1 quality layer remains present.
    assert request["style_dna"]["id"]
    assert request["long_term_memory"]["article_count"] >= 50
    assert request["title_selection"]["internal_candidate_count"] == 5

    # Existing safety / side-effect behavior remains unchanged.
    assert request["automatic_retry"] is False
    assert request["website_sync"] is False
    assert request["scheduled"] is False
    assert request["published"] is False
    assert any("不得引用" in item and "历史频数" in item for item in request["creative_mandate"])
    assert any("不断更换参数" in item for item in request["creative_mandate"])
