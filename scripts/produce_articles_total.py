from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.production_controller import (
    ProductionControllerError,
    build_production_plan,
    execute_production_plan,
    load_controller_policy,
)
from engine.production_evidence import generate_article_for_production
from engine.provider_transport import make_responses_transport, normalize_base_url
from engine.seo_priority import read_demand_signals


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _plan_for_disk(plan: dict) -> dict:
    safe = {key: value for key, value in plan.items() if key != "candidates"}
    safe["candidate_preview"] = [
        {
            "article_id": row["blueprint"].get("article_id"),
            "primary_keyword": row["blueprint"].get("primary_keyword"),
            "subject_lottery": row["blueprint"].get("subject_lottery"),
            "subject_play": row["blueprint"].get("subject_play"),
            "technique_atoms": row["blueprint"].get("technique_atoms", []),
            "primary_filter_spec": row["blueprint"].get("primary_filter_spec"),
            "priority_score": row.get("priority_score"),
            "priority_band": row.get("priority_band"),
        }
        for row in plan.get("candidates", [])[:50]
    ]
    safe["candidate_preview_truncated"] = len(plan.get("candidates", [])) > 50
    return safe


def _build_plan_with_capacity_retry(
    target: int,
    *,
    provider_id: str,
    signals: list[dict],
    batch_size: int | None,
    allow_ultra: bool,
) -> dict:
    """Build a normal plan, then deepen only when the first probe is truncated and insufficient.

    The first pass stays cheap. A second pass uses the policy's deep-probe
    multiplier so a low shallow count cannot be mistaken for exhausted content
    space. No model/provider call happens in either pass.
    """
    policy = load_controller_policy()
    plan = build_production_plan(
        target,
        provider_id=provider_id,
        signals=signals,
        batch_size=batch_size,
        allow_ultra=allow_ultra,
        policy=policy,
    )
    should_retry = bool(policy.get("capacity_retry_when_truncated_and_below_target", True)) and (
        not plan.get("capacity_exhaustive", False)
        and not plan.get("target_feasible_current_snapshot", False)
    )
    if not should_retry:
        plan["capacity_probe_passes"] = 1
        return plan

    deep_policy = dict(policy)
    deep_multiplier = max(
        int(policy.get("candidate_attempt_multiplier") or 1),
        int(policy.get("capacity_deep_probe_multiplier") or 50),
    )
    deep_policy["candidate_attempt_multiplier"] = deep_multiplier
    deep_plan = build_production_plan(
        target,
        provider_id=provider_id,
        signals=signals,
        batch_size=batch_size,
        allow_ultra=allow_ultra,
        policy=deep_policy,
    )
    deep_plan["capacity_probe_passes"] = 2
    deep_plan["capacity_initial_snapshot"] = {
        "candidate_count": plan.get("candidate_capacity_current_snapshot"),
        "capacity_exhaustive": plan.get("capacity_exhaustive"),
        "target_feasible": plan.get("target_feasible_current_snapshot"),
    }
    return deep_plan


def _provider_transport_from_environment():
    """Use the repository's configured OpenAI-compatible provider when supplied.

    The API key remains read by the generation layer from OPENAI_API_KEY. This
    helper only selects the endpoint transport and never logs credentials.
    """
    raw_base_url = os.getenv("OPENAI_BASE_URL")
    if not raw_base_url:
        return None, None
    base_url = normalize_base_url(raw_base_url)
    return make_responses_transport(base_url), base_url


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Article Production Controller: capacity preflight -> batched generation -> Approval -> formal Approved inventory."
    )
    parser.add_argument("target", type=int, help="number of NEW formal Approved Package files requested")
    parser.add_argument("--provider-id", default="", help="optional platform provider id for verified economics; mechanics-only is allowed")
    parser.add_argument("--signals", type=Path, help="optional real SEO demand signals JSON/JSONL")
    parser.add_argument("--batch-size", type=int, help="internal batch size; policy normally allows 20-30")
    parser.add_argument("--model", help="OpenAI model override")
    parser.add_argument("--allow-ultra", action="store_true", help="explicitly allow a target above the large-task threshold after capacity preflight")
    parser.add_argument("--execute", action="store_true", help="actually call the model, record Approval lifecycle, and stage formal Approved Packages")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    signals = read_demand_signals(args.signals)
    try:
        plan = _build_plan_with_capacity_retry(
            args.target,
            provider_id=args.provider_id,
            signals=signals,
            batch_size=args.batch_size,
            allow_ultra=args.allow_ultra,
        )
    except ProductionControllerError as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir or Path("runs") / f"production-controller-{stamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    _write(output_dir / "plan.json", _plan_for_disk(plan))

    summary = {
        "status": "PLAN_READY",
        "target": plan["target_new_formal_articles"],
        "target_band": plan["target_band"],
        "batch_size": plan["batch_size"],
        "candidate_capacity_current_snapshot": plan["candidate_capacity_current_snapshot"],
        "capacity_exhaustive": plan["capacity_exhaustive"],
        "target_feasible_current_snapshot": plan["target_feasible_current_snapshot"],
        "capacity_probe_passes": plan.get("capacity_probe_passes", 1),
        "attempt_budget": plan["attempt_budget"],
        "formal_inventory_before": plan["formal_inventory_before"],
        "execute_requested": bool(args.execute),
        "website_sync_allowed": False,
        "scheduling_allowed": False,
        "publishing_allowed": False,
        "output_dir": str(output_dir),
    }
    if plan.get("capacity_initial_snapshot"):
        summary["capacity_initial_snapshot"] = plan["capacity_initial_snapshot"]

    if not args.execute:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    transport, base_url = _provider_transport_from_environment()
    summary["model_provider_transport"] = "configured_compatible_endpoint" if transport else "default_openai_endpoint"
    if base_url:
        summary["model_provider_base_url"] = base_url

    result = execute_production_plan(
        plan,
        model=args.model,
        transport=transport,
        generate_fn=generate_article_for_production,
    )
    _write(output_dir / "result.json", result)
    summary.update({
        "status": result["status"],
        "stop_reason": result["stop_reason"],
        "attempted": result["attempted"],
        "generated": result["generated"],
        "approved": result["approved"],
        "formal_inventory_staged": result["formal_inventory_staged"],
        "approval_failed": result["approval_failed"],
        "generation_failed": result["generation_failed"],
        "reader_terminology_failed": result["reader_terminology_failed"],
        "formal_inventory_error_count": result["formal_inventory_error_count"],
        "quality_score_average": result["quality_score_average"],
        "editorial_score_average": result["editorial_score_average"],
    })
    _write(output_dir / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if result["formal_inventory_error_count"]:
        return 7
    return 0 if result["formal_inventory_staged"] > 0 else 6


if __name__ == "__main__":
    raise SystemExit(main())
