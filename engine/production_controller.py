from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Callable

from .ai_generation import GenerationError, generate_article
from .approval import evaluate_and_record
from .blueprints import blueprint_from_plan
from .draft_packets import build_case_bundle, build_draft_packet
from .formal_approved_inventory import FormalInventoryError, stage_formal_approved_package
from .generation_normalization import normalize_generation_metadata
from .planner import plan_articles
from .production_filter_contract import ProductionFilterContractError, build_primary_filter_spec
from .public_terminology import audit_article
from .rules import load_rules
from .seo_keywords import normalize_keyword
from .seo_priority import rank_blueprints
from .store import ROOT

POLICY_PATH = ROOT / "policies" / "ARTICLE_PRODUCTION_CONTROLLER.json"
FORMAL_APPROVED_ROOT = ROOT / "articles" / "approved"


class ProductionControllerError(ValueError):
    pass


def load_controller_policy(path: Path | None = None) -> dict:
    path = path or POLICY_PATH
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or int(data.get("version") or 0) < 1:
        raise ProductionControllerError("invalid article production controller policy")
    for field in ("default_target", "ordinary_target_max", "large_target_max", "internal_batch_default"):
        if int(data.get(field) or 0) <= 0:
            raise ProductionControllerError(f"invalid controller policy field: {field}")
    return data


def target_band(target: int, policy: dict | None = None) -> str:
    policy = policy or load_controller_policy()
    if target <= 0:
        raise ProductionControllerError("target must be positive")
    if target <= int(policy["ordinary_target_max"]):
        return "ordinary"
    if target <= int(policy["large_target_max"]):
        return "large"
    return "ultra"


def resolve_batch_size(target: int, requested: int | None = None, policy: dict | None = None) -> int:
    policy = policy or load_controller_policy()
    if target <= 0:
        raise ProductionControllerError("target must be positive")
    minimum = int(policy["internal_batch_min"])
    maximum = int(policy["internal_batch_max"])
    value = int(requested or policy["internal_batch_default"])
    if target < minimum:
        return target
    if value < minimum or value > maximum:
        raise ProductionControllerError(f"internal batch size must be between {minimum} and {maximum}")
    return value


def partition_batches(total: int, batch_size: int) -> list[int]:
    if total <= 0:
        return []
    if batch_size <= 0:
        raise ProductionControllerError("batch_size must be positive")
    full, remainder = divmod(total, batch_size)
    batches = [batch_size] * full
    if remainder:
        batches.append(remainder)
    return batches


def _verified_mechanics_work_units() -> list[dict]:
    units: dict[tuple[str, str], dict] = {}
    for rule in load_rules():
        if rule.get("status") != "verified" or rule.get("scope", "full") not in {"mechanics", "full"}:
            continue
        lottery = str(rule.get("lottery") or "").strip()
        play = str(rule.get("play") or "").strip()
        if not lottery or not play:
            continue
        units.setdefault((lottery, play), {"lottery": lottery, "play": play})
    return sorted(units.values(), key=lambda row: (row["lottery"], row["play"]))


def _formal_inventory_records(root: Path = FORMAL_APPROVED_ROOT) -> list[dict]:
    rows: list[dict] = []
    if not root.exists():
        return rows
    for path in sorted(root.glob("*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def formal_inventory_count(root: Path = FORMAL_APPROVED_ROOT) -> int:
    return len(_formal_inventory_records(root))


def _structural_key(record: dict) -> tuple:
    return (
        str(record.get("subject_lottery") or record.get("lottery") or ""),
        str(record.get("subject_play") or record.get("play") or ""),
        tuple(sorted(str(x) for x in record.get("technique_atoms", []) if str(x))),
        str(record.get("resolved_selector") or ""),
        str(record.get("case_structure") or ""),
    )


def _public_subject(lottery: str, policy: dict) -> str:
    aliases = policy.get("default_public_subject_aliases", {})
    return str(aliases.get(lottery, lottery))


def _assign_cluster_metadata(blueprint: dict, policy: dict) -> None:
    subject = str(blueprint.get("subject_lottery") or "")
    primary = policy.get("default_primary_cluster_by_public_subject", {}).get(subject)
    if primary:
        blueprint["primary_seo_cluster_id"] = str(primary)
        blueprint["secondary_seo_cluster_ids"] = []


def _bind_primary_filter_contract(blueprint: dict) -> None:
    case_bundle = build_case_bundle(blueprint)
    spec = build_primary_filter_spec(blueprint, case_bundle)
    blueprint["primary_filter_spec"] = spec


def discover_candidate_portfolio(
    target: int,
    *,
    provider_id: str = "",
    signals: list[dict] | None = None,
    policy: dict | None = None,
) -> dict:
    policy = policy or load_controller_policy()
    units = _verified_mechanics_work_units()
    existing = _formal_inventory_records()
    existing_ids = {str(row.get("article_id") or "") for row in existing}
    existing_keywords = {normalize_keyword(row.get("primary_keyword")) for row in existing if row.get("primary_keyword")}
    existing_structures = {_structural_key(row) for row in existing}
    if not units:
        return {
            "work_units": [], "candidate_count": 0, "candidates": [],
            "capacity_exhaustive": True, "probe_per_work_unit": 0,
        }

    multiplier = max(1, int(policy.get("candidate_attempt_multiplier") or 3))
    desired_pool = max(target, target * multiplier)
    max_probe = max(1, int(policy.get("capacity_probe_per_work_unit_max") or 1000))
    probe = min(max_probe, max(50, math.ceil(desired_pool / len(units)) * 2))

    raw_candidates: list[dict] = []
    unit_reports: list[dict] = []
    truncated = False
    for unit in units:
        result = plan_articles(provider_id, unit["lottery"], unit["play"], probe)
        plans = result.get("plans", [])
        if len(plans) >= probe:
            truncated = True
        ready_here = 0
        contract_blocked_here = 0
        for plan in plans:
            enriched_plan = dict(plan)
            enriched_plan["subject_lottery"] = _public_subject(unit["lottery"], policy)
            enriched_plan["subject_play"] = unit["play"]
            blueprint = blueprint_from_plan(enriched_plan)
            _assign_cluster_metadata(blueprint, policy)
            if blueprint.get("status") != "ready_for_draft":
                continue
            if blueprint.get("article_id") in existing_ids:
                continue
            keyword = normalize_keyword(blueprint.get("primary_keyword"))
            if keyword and keyword in existing_keywords:
                continue
            if _structural_key(blueprint) in existing_structures:
                continue
            try:
                _bind_primary_filter_contract(blueprint)
            except ProductionFilterContractError:
                contract_blocked_here += 1
                continue
            score_row = rank_blueprints([blueprint], signals)[0]
            if not score_row.get("eligible"):
                continue
            raw_candidates.append({
                "priority_score": float(score_row.get("priority_score") or 0),
                "priority_band": score_row.get("priority_band"),
                "blueprint": blueprint,
            })
            ready_here += 1
        unit_reports.append({
            **unit,
            "planner_status": result.get("status"),
            "plans_seen": len(plans),
            "ready_candidates_before_global_dedup": ready_here,
            "primary_filter_contract_blocked": contract_blocked_here,
        })

    raw_candidates.sort(key=lambda row: row["priority_score"], reverse=True)
    candidates: list[dict] = []
    seen_ids: set[str] = set()
    seen_keywords: set[str] = set()
    seen_structures: set[tuple] = set()
    for row in raw_candidates:
        blueprint = row["blueprint"]
        article_id = str(blueprint.get("article_id") or "")
        keyword = normalize_keyword(blueprint.get("primary_keyword"))
        structure = _structural_key(blueprint)
        if not article_id or article_id in seen_ids:
            continue
        if keyword and keyword in seen_keywords:
            continue
        if structure in seen_structures:
            continue
        seen_ids.add(article_id)
        if keyword:
            seen_keywords.add(keyword)
        seen_structures.add(structure)
        candidates.append(row)

    return {
        "work_units": unit_reports,
        "work_unit_count": len(units),
        "probe_per_work_unit": probe,
        "capacity_exhaustive": not truncated,
        "candidate_count": len(candidates),
        "candidates": candidates,
    }


def build_production_plan(
    target: int,
    *,
    provider_id: str = "",
    signals: list[dict] | None = None,
    batch_size: int | None = None,
    allow_ultra: bool = False,
    policy: dict | None = None,
) -> dict:
    policy = policy or load_controller_policy()
    band = target_band(target, policy)
    if band == "ultra" and policy.get("ultra_target_requires_explicit_opt_in", True) and not allow_ultra:
        raise ProductionControllerError(
            f"target {target} exceeds large_target_max={policy['large_target_max']}; explicit ultra opt-in required"
        )
    resolved_batch = resolve_batch_size(target, batch_size, policy)
    portfolio = discover_candidate_portfolio(
        target,
        provider_id=provider_id,
        signals=signals,
        policy=policy,
    )
    candidate_count = int(portfolio["candidate_count"])
    attempt_multiplier = max(1, int(policy.get("candidate_attempt_multiplier") or 3))
    attempt_budget = min(candidate_count, target * attempt_multiplier)
    feasible = candidate_count >= target
    return {
        "controller_version": int(policy["version"]),
        "target_new_formal_articles": target,
        "target_band": band,
        "recommended_range": [int(policy["recommended_target_min"]), int(policy["recommended_target_max"])],
        "ordinary_target_max": int(policy["ordinary_target_max"]),
        "large_target_max": int(policy["large_target_max"]),
        "batch_size": resolved_batch,
        "target_batches": partition_batches(target, resolved_batch),
        "provider_id": provider_id,
        "formal_inventory_before": formal_inventory_count(),
        "candidate_capacity_current_snapshot": candidate_count,
        "capacity_exhaustive": bool(portfolio["capacity_exhaustive"]),
        "target_feasible_current_snapshot": feasible,
        "attempt_budget": attempt_budget,
        "attempt_batches": partition_batches(attempt_budget, resolved_batch),
        "work_units": portfolio["work_units"],
        "candidates": portfolio["candidates"][:attempt_budget],
        "stop_if_capacity_exhausted": True,
        "quality_floor_lowering_allowed": False,
        "website_sync_allowed": False,
        "scheduling_allowed": False,
        "publishing_allowed": False,
    }


def _packet_with_cluster_metadata(blueprint: dict) -> dict:
    packet = build_draft_packet(blueprint)
    facts = packet.setdefault("immutable_facts", {})
    if blueprint.get("primary_seo_cluster_id"):
        facts["primary_seo_cluster_id"] = blueprint["primary_seo_cluster_id"]
        facts["secondary_seo_cluster_ids"] = list(blueprint.get("secondary_seo_cluster_ids", []))
    claims = packet.setdefault("claims", {})
    claims["forbidden_literal_terms_even_when_negated"] = list(claims.get("forbidden_terms", []))
    claims["editorial_scope_claim_evidence_rule"] = (
        "纯编辑范围/风险说明使用 claim_type=editorial, support_type=editorial, support_refs=[]；"
        "不要因为 packet 同时有 source_refs 就把这类句子标成 source_unverified。"
    )
    return packet


def execute_production_plan(
    plan: dict,
    *,
    model: str | None = None,
    api_key: str | None = None,
    transport=None,
    generate_fn: Callable = generate_article,
    approve_fn: Callable = evaluate_and_record,
    stage_fn: Callable = stage_formal_approved_package,
) -> dict:
    target = int(plan["target_new_formal_articles"])
    batch_size = int(plan["batch_size"])
    candidates = list(plan.get("candidates", []))
    staged = 0
    unchanged = 0
    attempted = 0
    generated = 0
    approved = 0
    approval_failed = 0
    generation_failed = 0
    terminology_failed = 0
    inventory_errors: list[dict] = []
    rows: list[dict] = []
    zero_progress_batches = 0
    stop_reason = "candidate_capacity_exhausted"

    for start in range(0, len(candidates), batch_size):
        if staged >= target:
            stop_reason = "target_reached"
            break
        batch = candidates[start:start + batch_size]
        batch_staged_before = staged
        for candidate in batch:
            if staged >= target:
                stop_reason = "target_reached"
                break
            blueprint = candidate["blueprint"]
            article_id = str(blueprint.get("article_id") or "")
            attempted += 1
            packet = _packet_with_cluster_metadata(blueprint)
            try:
                generation = generate_fn(packet, model=model, api_key=api_key, transport=transport)
            except GenerationError as exc:
                generation_failed += 1
                rows.append({"article_id": article_id, "status": "generation_failed", "error": str(exc)})
                continue

            generated += 1
            article = normalize_generation_metadata(generation.article)
            approval = approve_fn(packet, article)
            if not approval.approved or not approval.publish_package:
                approval_failed += 1
                rows.append({
                    "article_id": article_id,
                    "status": approval.status,
                    "approved": False,
                    "quality_score": approval.quality_score,
                    "editorial_score": approval.editorial_score,
                    "errors": approval.errors,
                })
                continue

            approved += 1
            package = approval.publish_package
            terminology = audit_article(f"controller:{article_id}", package)
            terminology_errors = [row.message for row in terminology if row.severity == "error"]
            if terminology_errors:
                terminology_failed += 1
                rows.append({
                    "article_id": article_id,
                    "status": "reader_terminology_rejected",
                    "approved": True,
                    "quality_score": approval.quality_score,
                    "editorial_score": approval.editorial_score,
                    "errors": terminology_errors,
                })
                continue

            try:
                inventory = stage_fn(package)
            except FormalInventoryError as exc:
                error = {"article_id": article_id, "error": str(exc)}
                inventory_errors.append(error)
                rows.append({"article_id": article_id, "status": "formal_inventory_error", "error": str(exc)})
                stop_reason = "formal_inventory_error"
                break

            if inventory.get("status") == "staged":
                staged += 1
            elif inventory.get("status") == "unchanged":
                unchanged += 1
            rows.append({
                "article_id": article_id,
                "status": inventory.get("status"),
                "approved": True,
                "quality_score": approval.quality_score,
                "editorial_score": approval.editorial_score,
                "primary_keyword": package.get("primary_keyword"),
                "subject_lottery": package.get("subject_lottery") or blueprint.get("subject_lottery"),
                "subject_play": package.get("subject_play") or blueprint.get("subject_play"),
                "primary_seo_cluster_id": package.get("primary_seo_cluster_id"),
            })

        if inventory_errors:
            break
        if staged == batch_staged_before:
            zero_progress_batches += 1
        else:
            zero_progress_batches = 0
        if zero_progress_batches >= 3:
            stop_reason = "three_consecutive_zero_progress_batches"
            break

    if staged >= target:
        stop_reason = "target_reached"

    successful_rows = [row for row in rows if row.get("status") == "staged"]
    play_distribution = Counter(str(row.get("subject_play") or "unassigned") for row in successful_rows)
    cluster_distribution = Counter(str(row.get("primary_seo_cluster_id") or "unassigned") for row in successful_rows)
    quality_scores = [int(row["quality_score"]) for row in successful_rows if row.get("quality_score") is not None]
    editorial_scores = [int(row["editorial_score"]) for row in successful_rows if row.get("editorial_score") is not None]

    return {
        "status": "PASS_TARGET_REACHED" if staged >= target else "PARTIAL_STOPPED",
        "stop_reason": stop_reason,
        "target_new_formal_articles": target,
        "attempted": attempted,
        "generated": generated,
        "approved": approved,
        "formal_inventory_staged": staged,
        "formal_inventory_unchanged": unchanged,
        "generation_failed": generation_failed,
        "approval_failed": approval_failed,
        "reader_terminology_failed": terminology_failed,
        "formal_inventory_error_count": len(inventory_errors),
        "formal_inventory_errors": inventory_errors,
        "formal_inventory_after": formal_inventory_count(),
        "quality_score_average": round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else None,
        "editorial_score_average": round(sum(editorial_scores) / len(editorial_scores), 2) if editorial_scores else None,
        "play_distribution": dict(play_distribution),
        "primary_cluster_distribution": dict(cluster_distribution),
        "website_sync_attempted": False,
        "scheduled": False,
        "published": False,
        "results": rows,
    }
