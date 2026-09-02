from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .ai_generation import GenerationError
from .daily_website_ready import (
    DailyProductionError,
    POLICY_PATH,
    REPORT_ROOT,
    _batch_id,
    _keyword_allowed,
    _write_report,
    choose_model,
    generate_public_release,
    load_daily_policy,
    production_date,
)
from .formal_approved_inventory import stage_formal_approved_package
from .production_controller import build_production_plan, execute_production_plan
from .provider_transport import DEFAULT_OPENAI_BASE_URL, make_responses_transport
from .public_release_revision import stage_public_release_revision, write_public_release_manifest
from .store import ROOT

PASS_STATUSES = {"PASS_TARGET", "PASS_PARTIAL_QUALITY_FIRST"}


def _status_for_ready(ready: int, *, target: int, minimum: int) -> str:
    if ready >= target:
        return "PASS_TARGET"
    if ready >= minimum:
        return "PASS_PARTIAL_QUALITY_FIRST"
    return "BLOCKED_BELOW_MINIMUM"


def _mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


def _fatal_report(day: str, policy: dict, exc: Exception) -> dict:
    return {
        "schema_version": 2,
        "date": day,
        "timezone": policy.get("timezone", "Asia/Singapore"),
        "batch_id": _batch_id(day),
        "status": "FATAL_ERROR",
        "target": int(policy.get("target") or 20),
        "minimum": int(policy.get("minimum") or 10),
        "maximum": int(policy.get("maximum") or 25),
        "website_ready_public_r1": 0,
        "quality_floor_lowered": False,
        "website_sync_attempted": False,
        "scheduled": False,
        "published": False,
        "error": str(exc),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }


def run_daily_refill(*, now: datetime | None = None, policy_path: Path | None = None) -> dict:
    policy = load_daily_policy(policy_path)
    day = production_date(now, str(policy["timezone"]))
    report_path = REPORT_ROOT / f"{day}.json"
    if report_path.is_file():
        prior = json.loads(report_path.read_text(encoding="utf-8"))
        if prior.get("status") in PASS_STATUSES:
            return {"status": "ALREADY_COMPLETED", "date": day, "report_path": str(report_path)}

    api_key = os.getenv("OPENAI_API_KEY") or ""
    if not api_key:
        raise DailyProductionError("MODEL_PROVIDER_API_KEY is not configured")
    base_url = (os.getenv("OPENAI_BASE_URL") or DEFAULT_OPENAI_BASE_URL).strip()
    model = choose_model(
        api_key,
        base_url,
        (os.getenv("OPENAI_MODEL") or "").strip() or None,
        [str(x) for x in policy.get("model_preference_hints", ["mini", "flash", "small", "lite"])],
    )

    batch_id = _batch_id(day)
    target = int(policy["target"])
    minimum = int(policy["minimum"])
    maximum = int(policy["maximum"])
    max_rounds = max(1, int(policy.get("max_refill_rounds") or 4))
    approved_batch_size = max(1, int(policy.get("refill_approved_batch_size") or 20))
    max_approved = max(target, int(policy.get("max_approved_parents_per_day") or 80))
    max_generation_attempts = max(target, int(policy.get("max_model_generation_attempts_per_day") or 120))
    candidate_pool_per_round = max(target, int(policy.get("candidate_pool") or 40))

    frozen = {str(x) for x in policy.get("frozen_article_ids", [])}
    attempted_ids: set[str] = set()
    public_ready: list[dict] = []
    public_failed: list[dict] = []
    rounds: list[dict] = []
    quality_scores: list[float] = []
    editorial_scores: list[float] = []
    play_distribution: Counter[str] = Counter()
    angle_distribution: Counter[str] = Counter()

    total_attempted = 0
    total_generated = 0
    total_approved = 0
    total_staged = 0
    total_approval_failed = 0
    total_generation_failed = 0
    total_duplicate_blocked = 0
    stop_reason = "refill_round_limit_reached"

    def stage_with_batch(package: dict) -> dict:
        enriched = dict(package)
        enriched["creator_batch_id"] = batch_id
        enriched.setdefault("creator_first_contract_version", "1.0")
        return stage_formal_approved_package(enriched)

    transport = make_responses_transport(base_url)

    for round_index in range(1, max_rounds + 1):
        if len(public_ready) >= target:
            stop_reason = "website_ready_target_reached"
            break
        if total_staged >= max_approved:
            stop_reason = "approved_parent_daily_cap_reached"
            break
        if total_attempted >= max_generation_attempts:
            stop_reason = "model_generation_attempt_cap_reached"
            break

        round_approved_target = min(approved_batch_size, max_approved - total_staged)
        plan = build_production_plan(
            round_approved_target,
            provider_id="",
            batch_size=min(int(policy.get("internal_batch_size") or 20), round_approved_target),
        )
        candidates: list[dict] = []
        remaining_attempt_budget = max_generation_attempts - total_attempted
        candidate_limit = min(candidate_pool_per_round, remaining_attempt_budget)
        for row in plan.get("candidates", []):
            blueprint = row.get("blueprint") or {}
            article_id = str(blueprint.get("article_id") or "")
            if not article_id or article_id in attempted_ids or article_id in frozen:
                continue
            if not _keyword_allowed(str(blueprint.get("primary_keyword") or ""), policy):
                continue
            candidates.append(row)
            if len(candidates) >= candidate_limit:
                break

        if not candidates:
            stop_reason = "candidate_capacity_exhausted"
            rounds.append({
                "round": round_index,
                "status": "NO_CANDIDATES",
                "website_ready_before": len(public_ready),
                "website_ready_after": len(public_ready),
            })
            break

        plan["candidates"] = candidates
        plan["attempt_budget"] = len(candidates)
        plan["target_new_formal_articles"] = round_approved_target
        result = execute_production_plan(
            plan,
            model=model,
            api_key=api_key,
            transport=transport,
            stage_fn=stage_with_batch,
        )

        rows = list(result.get("results", []))
        for row in rows:
            article_id = str(row.get("article_id") or "")
            if article_id:
                attempted_ids.add(article_id)
            if row.get("status") == "staged":
                if row.get("quality_score") is not None:
                    quality_scores.append(float(row["quality_score"]))
                if row.get("editorial_score") is not None:
                    editorial_scores.append(float(row["editorial_score"]))
                play_distribution[str(row.get("subject_play") or "unassigned")] += 1
                angle_distribution[str(row.get("information_gain_type") or "legacy")] += 1

        total_attempted += int(result.get("attempted") or 0)
        total_generated += int(result.get("generated") or 0)
        total_approved += int(result.get("approved") or 0)
        total_approval_failed += int(result.get("approval_failed") or 0)
        total_generation_failed += int(result.get("generation_failed") or 0)
        total_duplicate_blocked += int(result.get("pre_generation_duplicate_blocked") or 0)

        staged_ids = [
            str(row["article_id"])
            for row in rows
            if row.get("status") == "staged" and row.get("article_id")
        ]
        total_staged += len(staged_ids)
        ready_before = len(public_ready)
        failed_before = len(public_failed)

        for article_id in staged_ids:
            if len(public_ready) >= maximum:
                stop_reason = "website_ready_maximum_reached"
                break
            parent_path = ROOT / "articles" / "approved" / f"{article_id}.json"
            parent = json.loads(parent_path.read_text(encoding="utf-8"))
            try:
                revision = generate_public_release(
                    parent,
                    api_key=api_key,
                    base_url=base_url,
                    model=model,
                    policy=policy,
                )
                staged_release = stage_public_release_revision(revision)
                public_ready.append({
                    "article_id": article_id,
                    "primary_keyword": parent.get("primary_keyword"),
                    "path": staged_release.get("path"),
                    "revision_id": staged_release.get("revision_id"),
                    "round": round_index,
                })
            except (DailyProductionError, GenerationError, ValueError) as exc:
                public_failed.append({
                    "article_id": article_id,
                    "round": round_index,
                    "error": str(exc),
                })

        round_report = {
            "round": round_index,
            "status": result.get("status"),
            "production_stop_reason": result.get("stop_reason"),
            "candidate_count_offered": len(candidates),
            "attempted": int(result.get("attempted") or 0),
            "generated": int(result.get("generated") or 0),
            "approved": int(result.get("approved") or 0),
            "approved_staged": len(staged_ids),
            "approval_failed": int(result.get("approval_failed") or 0),
            "generation_failed": int(result.get("generation_failed") or 0),
            "website_ready_before": ready_before,
            "website_ready_added": len(public_ready) - ready_before,
            "website_ready_after": len(public_ready),
            "public_release_failed_added": len(public_failed) - failed_before,
            "quality_score_average": result.get("quality_score_average"),
            "editorial_score_average": result.get("editorial_score_average"),
        }
        rounds.append(round_report)

        interim = {
            "schema_version": 2,
            "date": day,
            "timezone": policy["timezone"],
            "batch_id": batch_id,
            "status": "IN_PROGRESS_REFILL",
            "target": target,
            "minimum": minimum,
            "maximum": maximum,
            "model": model,
            "base_url": base_url,
            "refill_rounds_completed": round_index,
            "max_refill_rounds": max_rounds,
            "approved_staged": total_staged,
            "website_ready_public_r1": len(public_ready),
            "public_release_failed": public_failed,
            "rounds": rounds,
            "quality_floor_lowered": False,
            "website_sync_attempted": False,
            "scheduled": False,
            "published": False,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        _write_report(day, interim)

        if len(public_ready) >= target:
            stop_reason = "website_ready_target_reached"
            break
        if total_staged == 0 and round_index == max_rounds:
            stop_reason = "no_approved_progress_before_round_limit"

    ready_count = len(public_ready)
    status = _status_for_ready(ready_count, target=target, minimum=minimum)
    manifest = None
    if ready_count >= minimum:
        manifest = write_public_release_manifest(batch_id, expected_count=ready_count)

    if status == "PASS_PARTIAL_QUALITY_FIRST" and stop_reason == "refill_round_limit_reached":
        stop_reason = "quality_first_partial_after_hard_cap"
    elif status == "BLOCKED_BELOW_MINIMUM" and stop_reason == "refill_round_limit_reached":
        stop_reason = "below_minimum_after_hard_cap"

    report = {
        "schema_version": 2,
        "date": day,
        "timezone": policy["timezone"],
        "batch_id": batch_id,
        "status": status,
        "target": target,
        "minimum": minimum,
        "maximum": maximum,
        "model": model,
        "base_url": base_url,
        "candidate_pool_per_round": candidate_pool_per_round,
        "max_refill_rounds": max_rounds,
        "max_approved_parents_per_day": max_approved,
        "max_model_generation_attempts_per_day": max_generation_attempts,
        "refill_rounds_completed": len(rounds),
        "attempted": total_attempted,
        "generated": total_generated,
        "approved": total_approved,
        "approved_staged": total_staged,
        "approval_failed": total_approval_failed,
        "generation_failed": total_generation_failed,
        "pre_generation_duplicate_blocked": total_duplicate_blocked,
        "website_ready_public_r1": ready_count,
        "public_release_failed_count": len(public_failed),
        "public_release_failed": public_failed,
        "stop_reason": stop_reason,
        "quality_score_average": _mean(quality_scores),
        "editorial_score_average": _mean(editorial_scores),
        "article_angle_distribution": dict(angle_distribution),
        "play_distribution": dict(play_distribution),
        "manifest": manifest,
        "website_sync_attempted": False,
        "scheduled": False,
        "published": False,
        "quality_floor_lowered": False,
        "public_ready": public_ready,
        "rounds": rounds,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    _write_report(day, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Daily final-public-r1-driven refill production")
    parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    args = parser.parse_args()
    try:
        policy = load_daily_policy(args.policy)
        day = production_date(None, str(policy["timezone"]))
        result = run_daily_refill(policy_path=args.policy)
    except (DailyProductionError, GenerationError, ValueError, OSError) as exc:
        try:
            policy = load_daily_policy(args.policy)
            day = production_date(None, str(policy["timezone"]))
            report = _fatal_report(day, policy, exc)
            _write_report(day, report)
        except Exception:
            report = {"status": "FATAL_ERROR", "error": str(exc)}
        print(json.dumps({"ok": False, **report}, ensure_ascii=False, indent=2))
        return 7

    ok = result.get("status") in PASS_STATUSES or result.get("status") == "ALREADY_COMPLETED"
    print(json.dumps({"ok": ok, **result}, ensure_ascii=False, indent=2))
    return 0 if ok else 7


if __name__ == "__main__":
    raise SystemExit(main())
