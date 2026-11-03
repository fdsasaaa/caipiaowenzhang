import copy
import json
from datetime import datetime, timezone

import pytest

import engine.daily_website_ready_refill as refill
from engine.daily_refill_diagnostics import (
    controller_diagnostics, error_category, select_candidates,
)
from engine.daily_website_ready import load_daily_policy


PRIVATE = "token=synthetic-secret https://example.invalid/?key=private person@example.invalid <p>private body</p>"


@pytest.mark.parametrize("message,expected", [
    ("model provider HTTP 429: " + PRIVATE, "provider_rate_limited"),
    ("model provider HTTP 401: " + PRIVATE, "provider_authentication"),
    ("model provider HTTP 403: " + PRIVATE, "provider_authorization"),
    ("model provider HTTP 500: " + PRIVATE, "provider_http"),
    ("model provider transport failed: " + PRIVATE, "provider_transport"),
    ("structured model output is not valid JSON " + PRIVATE, "structured_output"),
    ("claim_evidence[0] " + PRIVATE, "claim_evidence_gate"),
    ("angle_delivery.angle_type " + PRIVATE, "angle_contract_gate"),
    ("[V2.2] " + PRIVATE, "multistage_gate"),
    ("public release safety gate failed: " + PRIVATE, "public_release_gate"),
    (PRIVATE, "unclassified"),
    ({PRIVATE: PRIVATE}, "unclassified"),
])
def test_error_categories_never_copy_dynamic_content(message, expected):
    assert error_category(message) == expected


def candidate(article_id, keyword="allowed"):
    return {"blueprint": {"article_id": article_id, "primary_keyword": keyword}}


def assert_filter_conservation(counts):
    assert counts["input"] == counts["examined"] + counts["not_examined"]
    assert counts["examined"] == sum(counts[key] for key in (
        "missing_article_id", "already_attempted", "frozen", "keyword_blocked", "selected",
    ))


def test_filter_order_cap_and_empty_pool():
    rows = [candidate(""), candidate("seen", "blocked"), candidate("frozen", "blocked"),
            candidate("blocked", "blocked"), candidate("a"), candidate("b"), candidate("tail")]
    before = copy.deepcopy(rows)
    calls = []

    def allowed(keyword, policy):
        calls.append(keyword)
        return keyword != "blocked"

    selected, counts = select_candidates(rows, {"seen"}, {"seen", "frozen"}, {}, 2, allowed)
    assert selected == rows[4:6]
    assert rows == before
    assert calls == ["blocked", "allowed", "allowed"]
    assert counts == dict(input=7, examined=6, missing_article_id=1, already_attempted=1,
                          frozen=1, keyword_blocked=1, selected=2, not_examined=1)
    assert_filter_conservation(counts)
    selected, counts = select_candidates([], set(), set(), {}, 2, allowed)
    assert selected == []
    assert_filter_conservation(counts)


def test_outcomes_and_message_counts_are_distinct_and_bounded():
    result = {"multistage_failed": 1, "results": [
        {"status": "rejected_multistage", "errors": ["[V2.2] " + PRIVATE] * 2},
        {"status": "formal_inventory_error", "error": PRIVATE},
        {"status": PRIVATE, "error": {PRIVATE: PRIVATE}},
        {"status": "staged", "content": PRIVATE, "provider_response_id": PRIVATE},
    ]}
    before = copy.deepcopy(result)
    diag = controller_diagnostics(result)
    assert result == before
    assert diag["result_rows"] == sum(diag["outcome_counts"].values()) == 4
    assert diag["error_observations"] == sum(diag["error_category_counts"].values()) == 4
    assert diag["error_category_counts"] == {"multistage_gate": 2, "unclassified": 2}
    assert diag["outcome_counts"]["unknown"] == 1
    assert PRIVATE not in json.dumps(diag)


def test_synthetic_partial_run_preserves_counts_and_no_candidates_evidence(monkeypatch, tmp_path):
    policy = load_daily_policy()
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.invalid/v1")
    monkeypatch.setattr(refill, "ROOT", tmp_path)
    monkeypatch.setattr(refill, "REPORT_ROOT", tmp_path / "reports")
    monkeypatch.setattr(refill, "choose_model", lambda *a, **k: "synthetic-model")
    monkeypatch.setattr(refill, "make_responses_transport", lambda *a, **k: object())
    statuses = (["generation_failed"] * 4 + ["rejected_multistage"] * 2
                + ["rejected_for_revision"] * 18 + ["staged"] * 3
                + ["pre_generation_duplicate_blocked"])
    rows = [{"article_id": f"SYN-{i}", "status": status} for i, status in enumerate(statuses)]
    for row in rows:
        if row["status"] == "generation_failed":
            row["error"] = "model provider HTTP 429: " + PRIVATE
        elif row["status"] == "rejected_multistage":
            row["errors"] = ["[V2.2] " + PRIVATE]
        elif row["status"] == "rejected_for_revision":
            row["errors"] = ["claim_evidence[0] " + PRIVATE]
    candidates = [candidate(""), candidate(policy["frozen_article_ids"][0]),
                  candidate("blocked", policy["blocked_exact_primary_keywords"][0])]
    candidates += [candidate(row["article_id"]) for row in rows]
    monkeypatch.setattr(refill, "build_production_plan", lambda *a, **k: {"candidates": candidates})
    calls = []

    def execute(plan, **kwargs):
        calls.append(plan)
        assert [r["blueprint"]["article_id"] for r in plan["candidates"]] == [r["article_id"] for r in rows]
        parent_root = tmp_path / "articles" / "approved"
        parent_root.mkdir(parents=True)
        for row in rows:
            if row["status"] == "staged":
                (parent_root / (row["article_id"] + ".json")).write_text(json.dumps({"article_id": row["article_id"]}))
        return dict(status="PARTIAL_STOPPED", stop_reason="candidate_capacity_exhausted",
                    attempted=27, generated=23, approved=3, approval_failed=20,
                    generation_failed=4, multistage_failed=2, pre_generation_duplicate_blocked=1,
                    results=rows)

    monkeypatch.setattr(refill, "execute_production_plan", execute)
    monkeypatch.setattr(refill, "generate_public_release", lambda parent, **k: parent)
    monkeypatch.setattr(refill, "stage_public_release_revision", lambda revision: {})
    manifests = []

    def manifest(batch_id, expected_count):
        manifests.append(expected_count)
        return {"expected_count": expected_count}

    monkeypatch.setattr(refill, "write_public_release_manifest", manifest)
    reports = []
    monkeypatch.setattr(refill, "_write_report", lambda day, report: reports.append(copy.deepcopy(report)))
    result = refill.run_daily_refill(now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert len(calls) == 1
    assert manifests == [3]
    assert result["status"] == "PASS_PARTIAL_QUALITY_FIRST"
    assert result["below_operational_minimum"] is True
    assert result["stop_reason"] == "candidate_capacity_exhausted"
    assert result["attempted"] == result["generated"] + result["generation_failed"] == 27
    assert result["generated"] == result["approved"] + result["approval_failed"] == 23
    assert result["approved_staged"] == result["website_ready_public_r1"] == 3
    assert result["pre_generation_duplicate_blocked"] == 1
    for round_report in result["rounds"]:
        assert_filter_conservation(round_report["candidate_filter_counts"])
    assert result["rounds"][1]["status"] == "NO_CANDIDATES"
    assert result["rounds"][1]["candidate_filter_counts"]["already_attempted"] == 28
    diag = result["rounds"][0]["controller_diagnostics"]
    assert diag["multistage_failed"] == 2
    assert diag["result_rows"] == 28
    assert diag["error_observations"] == 24
    assert diag["error_category_counts"] == dict(provider_rate_limited=4, multistage_gate=2, claim_evidence_gate=18)
    assert reports[0]["rounds"][0]["controller_diagnostics"] == diag
    assert PRIVATE not in json.dumps(reports)
    assert not result["website_sync_attempted"] and not result["scheduled"] and not result["published"]


def test_fatal_report_drops_exception_text():
    report = refill._fatal_report("2026-01-01", load_daily_policy(), ValueError(PRIVATE))
    assert report["error"] == "unclassified"
    assert PRIVATE not in json.dumps(report)
