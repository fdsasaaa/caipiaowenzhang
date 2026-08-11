from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policies" / "BET_COMPLIANCE_POLICY.json"


@dataclass
class ComplianceReport:
    passed: bool
    violations: list[dict] = field(default_factory=list)
    groups: list[dict] = field(default_factory=list)


def load_policy() -> dict:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def _phase_amounts(bet: dict) -> dict[str, float]:
    phases = bet.get("phase_amounts")
    if isinstance(phases, dict) and phases:
        return {str(k): float(v) for k, v in phases.items()}
    return {"base": float(bet.get("stake_amount", 0.0))}


def _mapping_problem(bet: dict) -> str | None:
    required = ("bet_id", "draw_id", "lottery_id", "play_id", "target_space_id", "target_space_size", "covered_outcomes", "prize_amount")
    missing = [k for k in required if k not in bet]
    if missing:
        return "missing fields: " + ", ".join(missing)
    if not isinstance(bet.get("covered_outcomes"), (list, tuple, set)):
        return "covered_outcomes must be an explicit iterable of unique target outcomes"
    if int(bet.get("target_space_size", 0)) <= 0:
        return "target_space_size must be positive"
    return None


def validate_portfolio(bets: list[dict], policy: dict | None = None) -> ComplianceReport:
    policy = policy or load_policy()
    amount_limit = float(policy["amount_ratio_limit"])
    coverage_limit = float(policy["coverage_ratio_limit"])
    violations: list[dict] = []
    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)

    for bet in bets:
        problem = _mapping_problem(bet)
        if problem:
            violations.append({
                "code": "missing_target_space_mapping",
                "bet_id": bet.get("bet_id"),
                "reason": problem,
            })
            continue
        key = (str(bet["draw_id"]), str(bet["lottery_id"]), str(bet["target_space_id"]))
        grouped[key].append(bet)

    reports: list[dict] = []
    for (draw_id, lottery_id, target_space_id), rows in grouped.items():
        space_sizes = {int(x["target_space_size"]) for x in rows}
        prizes = {float(x["prize_amount"]) for x in rows}
        play_ids = sorted({str(x["play_id"]) for x in rows})
        if len(space_sizes) != 1:
            violations.append({
                "code": "ambiguous_target_space_size",
                "draw_id": draw_id,
                "lottery_id": lottery_id,
                "target_space_id": target_space_id,
                "values": sorted(space_sizes),
            })
            continue
        if len(prizes) != 1:
            violations.append({
                "code": "ambiguous_prize_reference",
                "draw_id": draw_id,
                "lottery_id": lottery_id,
                "target_space_id": target_space_id,
                "values": sorted(prizes),
            })
            continue

        target_space_size = next(iter(space_sizes))
        prize_amount = next(iter(prizes))
        covered: set[str] = set()
        phase_totals: dict[str, float] = defaultdict(float)
        for row in rows:
            covered.update(str(x) for x in row["covered_outcomes"])
            for phase, amount in _phase_amounts(row).items():
                phase_totals[phase] += amount

        coverage_ratio = len(covered) / target_space_size
        group_report = {
            "draw_id": draw_id,
            "lottery_id": lottery_id,
            "target_space_id": target_space_id,
            "play_ids": play_ids,
            "target_space_size": target_space_size,
            "unique_covered_outcomes": len(covered),
            "coverage_ratio": coverage_ratio,
            "prize_amount": prize_amount,
            "phase_totals": dict(sorted(phase_totals.items())),
        }
        reports.append(group_report)

        if coverage_ratio > coverage_limit:
            violations.append({
                "code": "cross_play_near_full_cover" if len(play_ids) > 1 else "coverage_limit_exceeded",
                "draw_id": draw_id,
                "lottery_id": lottery_id,
                "target_space_id": target_space_id,
                "play_ids": play_ids,
                "coverage_ratio": coverage_ratio,
                "limit": coverage_limit,
                "unique_covered_outcomes": len(covered),
                "target_space_size": target_space_size,
            })

        amount_ceiling = prize_amount * amount_limit
        for phase, total in phase_totals.items():
            if total > amount_ceiling:
                violations.append({
                    "code": "advanced_staking_amount_exceeded" if phase != "base" else "amount_limit_exceeded",
                    "draw_id": draw_id,
                    "lottery_id": lottery_id,
                    "target_space_id": target_space_id,
                    "phase": phase,
                    "total_amount": total,
                    "prize_amount": prize_amount,
                    "limit_amount": amount_ceiling,
                })

    return ComplianceReport(passed=not violations, violations=violations, groups=reports)


def assert_exportable(bets: list[dict], policy: dict | None = None) -> ComplianceReport:
    report = validate_portfolio(bets, policy)
    if not report.passed:
        reasons = "; ".join(v["code"] for v in report.violations)
        raise ValueError(f"export blocked by bet compliance policy: {reasons}")
    return report
