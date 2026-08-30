from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from .ai_generation import GenerationError
from .daily_website_ready import (
    DailyProductionError,
    POLICY_PATH,
    _write_report,
    load_daily_policy,
    production_date,
)
from .daily_website_ready_refill import PASS_STATUSES, _fatal_report, run_daily_refill
from .public_release_revision import write_public_release_manifest


def _retained_status(ready: int, *, target: int, commit_minimum: int) -> str:
    if ready >= target:
        return "PASS_TARGET"
    if ready >= commit_minimum:
        return "PASS_PARTIAL_QUALITY_FIRST"
    return "BLOCKED_EMPTY_QUALITY_BATCH"


def run_daily_partial(*, now: datetime | None = None, policy_path: Path | None = None) -> dict:
    policy = load_daily_policy(policy_path)
    commit_minimum = int(policy.get("commit_minimum") or 1)
    if commit_minimum < 1 or commit_minimum > int(policy["target"]):
        raise DailyProductionError("commit_minimum must satisfy 1 <= commit_minimum <= target")

    result = run_daily_refill(now=now, policy_path=policy_path)
    if result.get("status") == "ALREADY_COMPLETED":
        return result

    ready = int(result.get("website_ready_public_r1") or 0)
    target = int(policy["target"])
    operational_minimum = int(policy["minimum"])
    status = _retained_status(ready, target=target, commit_minimum=commit_minimum)

    result["commit_minimum"] = commit_minimum
    result["operational_minimum"] = operational_minimum
    result["partial_batch_retention"] = True
    result["retained_below_operational_minimum"] = (
        commit_minimum <= ready < operational_minimum
    )

    if status == "PASS_PARTIAL_QUALITY_FIRST" and result.get("manifest") is None:
        result["manifest"] = write_public_release_manifest(
            str(result["batch_id"]), expected_count=ready
        )
        result["stop_reason"] = "quality_first_partial_retained_after_refill_exhaustion"

    result["status"] = status
    day = str(result.get("date") or production_date(now, str(policy["timezone"])))
    _write_report(day, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Daily quality-first production with non-empty partial-batch retention"
    )
    parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    args = parser.parse_args()
    try:
        policy = load_daily_policy(args.policy)
        day = production_date(None, str(policy["timezone"]))
        result = run_daily_partial(policy_path=args.policy)
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
