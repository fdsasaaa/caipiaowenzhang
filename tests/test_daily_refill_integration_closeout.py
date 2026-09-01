import json
from pathlib import Path

import engine.daily_website_ready_refill as refill
from engine.daily_website_ready import DailyProductionError, load_daily_policy


def test_refill_continues_after_public_r1_rejection_until_final_target(monkeypatch, tmp_path):
    policy = load_daily_policy()
    policy.update({
        "minimum": 1,
        "operational_minimum": 2,
        "target": 3,
        "maximum": 4,
        "candidate_pool": 4,
        "internal_batch_size": 2,
        "refill_approved_batch_size": 2,
        "max_refill_rounds": 3,
        "max_approved_parents_per_day": 6,
        "max_model_generation_attempts_per_day": 10,
    })
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps(policy, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.invalid/v1")
    monkeypatch.setattr(refill, "ROOT", tmp_path)
    monkeypatch.setattr(refill, "REPORT_ROOT", tmp_path / "reports")
    monkeypatch.setattr(refill, "choose_model", lambda *args, **kwargs: "test-model")
    monkeypatch.setattr(refill, "make_responses_transport", lambda *args, **kwargs: object())

    build_calls = {"count": 0}

    def fake_build_production_plan(target, **kwargs):
        build_calls["count"] += 1
        round_no = build_calls["count"]
        candidates = []
        for index in range(1, 3):
            article_id = f"TEST-R{round_no}-{index}"
            candidates.append({
                "blueprint": {
                    "article_id": article_id,
                    "primary_keyword": f"分分彩结构研究{round_no}{index}",
                }
            })
        return {
            "batch_size": 2,
            "candidates": candidates,
            "target_new_formal_articles": target,
        }

    def fake_execute_production_plan(plan, **kwargs):
        approved_root = tmp_path / "articles" / "approved"
        approved_root.mkdir(parents=True, exist_ok=True)
        rows = []
        for candidate in plan["candidates"][:2]:
            blueprint = candidate["blueprint"]
            article_id = blueprint["article_id"]
            parent = {
                "article_id": article_id,
                "primary_keyword": blueprint["primary_keyword"],
                "creator_batch_id": "DAILY-TEST",
                "content_hash": f"hash-{article_id}",
                "fingerprint": f"fp-{article_id}",
            }
            (approved_root / f"{article_id}.json").write_text(
                json.dumps(parent, ensure_ascii=False), encoding="utf-8"
            )
            rows.append({
                "article_id": article_id,
                "status": "staged",
                "quality_score": 95,
                "editorial_score": 94,
                "subject_play": "后二直选",
                "information_gain_type": "structure",
            })
        return {
            "status": "PASS_TARGET_REACHED",
            "stop_reason": "target_reached",
            "attempted": 2,
            "generated": 2,
            "approved": 2,
            "approval_failed": 0,
            "generation_failed": 0,
            "pre_generation_duplicate_blocked": 0,
            "quality_score_average": 95,
            "editorial_score_average": 94,
            "results": rows,
        }

    def fake_generate_public_release(parent, **kwargs):
        if parent["article_id"] == "TEST-R1-2":
            raise DailyProductionError("synthetic public-r1 rejection")
        return {"article_id": parent["article_id"]}

    monkeypatch.setattr(refill, "build_production_plan", fake_build_production_plan)
    monkeypatch.setattr(refill, "execute_production_plan", fake_execute_production_plan)
    monkeypatch.setattr(refill, "generate_public_release", fake_generate_public_release)
    monkeypatch.setattr(
        refill,
        "stage_public_release_revision",
        lambda revision: {
            "path": f"public/{revision['article_id']}.json",
            "revision_id": f"{revision['article_id']}:public-r1",
        },
    )
    monkeypatch.setattr(
        refill,
        "write_public_release_manifest",
        lambda batch_id, expected_count: {"batch_id": batch_id, "expected_count": expected_count},
    )

    reports = []

    def capture_report(day, payload):
        reports.append(dict(payload))
        return tmp_path / "reports" / f"{day}.json"

    monkeypatch.setattr(refill, "_write_report", capture_report)

    result = refill.run_daily_refill(policy_path=policy_path)

    assert result["status"] == "PASS_TARGET"
    assert result["website_ready_public_r1"] == 3
    assert result["public_release_failed_count"] == 1
    assert result["refill_rounds_completed"] == 2
    assert result["rounds"][0]["website_ready_added"] == 1
    assert result["rounds"][1]["website_ready_added"] == 2
    assert result["stop_reason"] == "website_ready_target_reached"
    assert result["quality_floor_lowered"] is False
    assert result["partial_batch_retention"] is True
    assert result["quality_first"] is True
    assert result["website_sync_attempted"] is False
    assert build_calls["count"] == 2
    assert reports[-1]["status"] == "PASS_TARGET"
