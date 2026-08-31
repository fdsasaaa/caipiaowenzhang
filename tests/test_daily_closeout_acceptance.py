from engine.daily_website_ready import load_daily_policy
from engine.daily_website_ready_refill import _status_for_ready
from engine.store import ROOT


WORKFLOW = ROOT / ".github" / "workflows" / "daily-website-ready-production.yml"


def test_closeout_volume_and_quality_contract():
    policy = load_daily_policy()
    assert policy["timezone"] == "Asia/Singapore"
    # V3: minimum=1 (formal commit floor), operational_minimum=10 (health signal)
    assert (policy["minimum"], policy["target"], policy["maximum"]) == (1, 20, 25)
    assert policy["operational_minimum"] == 10
    assert policy["partial_batch_retention"] is True
    assert policy["quality_first"] is True
    assert policy["quality_floor_may_be_lowered"] is False
    assert policy["public_release_required_to_count"] is True
    assert policy["public_release_generation_attempts"] >= 3


def test_closeout_refill_and_cost_caps_are_bounded():
    policy = load_daily_policy()
    assert 2 <= policy["max_refill_rounds"] <= 6
    assert policy["refill_approved_batch_size"] >= 10
    assert policy["max_approved_parents_per_day"] >= policy["target"]
    assert policy["max_model_generation_attempts_per_day"] >= policy["max_approved_parents_per_day"]
    assert policy["max_model_generation_attempts_per_day"] <= 150


def test_closeout_final_public_r1_count_drives_status():
    # V3: minimum=1 is the formal floor; operational_minimum=10 is a health signal.
    # 0 qualified → FAIL CLOSED; 1+ qualified → PASS_PARTIAL; 20+ → PASS_TARGET
    assert _status_for_ready(0, minimum=1, target=20) == "BLOCKED_BELOW_MINIMUM"
    assert _status_for_ready(1, minimum=1, target=20) == "PASS_PARTIAL_QUALITY_FIRST"
    assert _status_for_ready(8, minimum=1, target=20) == "PASS_PARTIAL_QUALITY_FIRST"
    assert _status_for_ready(10, minimum=1, target=20) == "PASS_PARTIAL_QUALITY_FIRST"
    assert _status_for_ready(19, minimum=1, target=20) == "PASS_PARTIAL_QUALITY_FIRST"
    assert _status_for_ready(20, minimum=1, target=20) == "PASS_TARGET"


def test_closeout_frozen_tail_and_broad_funding_terms_remain_blocked():
    policy = load_daily_policy()
    frozen = set(policy["frozen_article_ids"])
    assert {
        "LCM-CREATOR-cf50-20260813-020",
        "LCM-CREATOR-cf50-20260813-029",
        "LCM-CREATOR-cf50-20260813-038",
        "LCM-CREATOR-cf50-20260813-039",
        "LCM-CREATOR-cf50-20260813-040",
    } <= frozen
    fragments = set(policy["blocked_primary_keyword_fragments"])
    assert {"倍投", "盈利", "赚钱", "资金管理"} <= fragments


def test_closeout_forbidden_website_side_effects_remain_explicit():
    policy = load_daily_policy()
    forbidden = set(policy["forbidden_side_effects"])
    assert {
        "website_sync",
        "website_cms_write",
        "website_schedule_creation",
        "publisher_invocation",
        "publisher_cron_change",
        "publication",
    } <= forbidden


def test_closeout_workflow_has_schedule_failure_evidence_ci_and_merge_order():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "cron: '20 1 * * *'" in text
    assert "MODEL_PROVIDER_API_KEY" in text
    assert "Produce and refill quality-first website-ready inventory" in text
    assert "Upload daily diagnostic artifact" in text
    assert "diagnostics/daily-website-ready-" in text
    assert "python -m engine.cli audit" in text
    assert "pytest -q" in text
    assert "gh workflow run test.yml --ref" in text
    assert "gh run watch \"$RUN_ID\" --exit-status" in text
    assert "gh pr merge \"$PR_URL\" --squash --delete-branch" in text
    assert "--admin" not in text
    assert text.index("Produce and refill quality-first website-ready inventory") < text.index("Run local full repository gates")
    assert text.index("Run local full repository gates") < text.index("Open daily production PR")
    assert text.index("Dispatch independent dual-version CI") < text.index("Squash merge only after CI passes")


def test_closeout_overlap_guard_and_fail_closed_are_present():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "A previous daily production PR is still open" in text
    assert "Daily branch exists without an open PR; fail closed" in text
    assert "Stop after failed quality-first production" in text
    assert "cancel-in-progress: false" in text
