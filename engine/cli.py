from __future__ import annotations

import argparse
import json

from .casebook import descriptive_case, frequency_case, omission_case
from .planner import plan_articles
from .rule_gaps import list_gaps, record_gap
from .rules import load_rules, rule_capability
from .store import counts, ensure_layout, rebuild_index


def cmd_init(_: argparse.Namespace) -> int:
    ensure_layout()
    result = rebuild_index()
    print(json.dumps({"initialized": True, "index": result}, ensure_ascii=False, indent=2))
    return 0


def cmd_status(_: argparse.Namespace) -> int:
    print(json.dumps({"registries": counts(), "rules": len(load_rules()), "rule_gaps": len(list_gaps())}, ensure_ascii=False, indent=2))
    return 0


def cmd_rebuild(_: argparse.Namespace) -> int:
    print(json.dumps(rebuild_index(), ensure_ascii=False, indent=2))
    return 0


def cmd_audit(_: argparse.Namespace) -> int:
    problems = []
    for rule in load_rules():
        scope = rule.get("scope", "full")
        required = ["rule_id", "lottery", "play", "status", "source"]
        if scope in {"economics", "full"}:
            required.append("provider_id")
        for field in required:
            if field not in rule:
                problems.append(f"rule missing {field}: {rule}")
        if rule.get("status") == "verified" and not rule.get("verified_at"):
            problems.append(f"verified rule missing verified_at: {rule.get('rule_id')}")
    result = {"ok": not problems, "problems": problems, "registry": counts(), "rule_gaps": len(list_gaps())}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not problems else 2


def cmd_plan(args: argparse.Namespace) -> int:
    result = plan_articles(args.provider, args.lottery, args.play, args.count)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked_mechanics_verification" else 3


def cmd_capability(args: argparse.Namespace) -> int:
    result = rule_capability(args.provider, args.lottery, args.play)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["mechanics_verified"] else 3


def cmd_record_gap(args: argparse.Namespace) -> int:
    row = record_gap(args.type, args.lottery, args.play, args.provider, args.reason)
    print(json.dumps(row, ensure_ascii=False, indent=2))
    return 0


def cmd_rule_gaps(_: argparse.Namespace) -> int:
    print(json.dumps(list_gaps(), ensure_ascii=False, indent=2))
    return 0


def cmd_case(args: argparse.Namespace) -> int:
    result = descriptive_case(args.draw, args.selector, args.lookback)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_omission_case(args: argparse.Namespace) -> int:
    result = omission_case(args.draw, args.position, args.threshold, args.lookback)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_frequency_case(args: argparse.Namespace) -> int:
    result = frequency_case(args.draw, args.selector, args.lookback, args.top)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _add_draw_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--draw", action="append", required=True, help="chronological draw, oldest to newest; repeat option")


def main() -> int:
    parser = argparse.ArgumentParser(prog="laocaimi-content-engine")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, fn in (("init", cmd_init), ("status", cmd_status), ("rebuild", cmd_rebuild), ("audit", cmd_audit), ("rule-gaps", cmd_rule_gaps)):
        p = sub.add_parser(name)
        p.set_defaults(func=fn)
    p = sub.add_parser("plan")
    p.add_argument("--provider", required=True)
    p.add_argument("--lottery", required=True)
    p.add_argument("--play", required=True)
    p.add_argument("--count", type=int, default=10)
    p.set_defaults(func=cmd_plan)
    p = sub.add_parser("capability")
    p.add_argument("--provider")
    p.add_argument("--lottery", required=True)
    p.add_argument("--play", required=True)
    p.set_defaults(func=cmd_capability)
    p = sub.add_parser("record-gap")
    p.add_argument("--type", choices=["mechanics", "economics"], required=True)
    p.add_argument("--provider")
    p.add_argument("--lottery", required=True)
    p.add_argument("--play", required=True)
    p.add_argument("--reason", default="")
    p.set_defaults(func=cmd_record_gap)
    p = sub.add_parser("case")
    _add_draw_args(p)
    p.add_argument("--selector", required=True)
    p.add_argument("--lookback", type=int)
    p.set_defaults(func=cmd_case)
    p = sub.add_parser("omission-case")
    _add_draw_args(p)
    p.add_argument("--position", required=True)
    p.add_argument("--threshold", type=int, required=True)
    p.add_argument("--lookback", type=int)
    p.set_defaults(func=cmd_omission_case)
    p = sub.add_parser("frequency-case")
    _add_draw_args(p)
    p.add_argument("--selector", required=True)
    p.add_argument("--lookback", type=int, required=True)
    p.add_argument("--top", type=int)
    p.set_defaults(func=cmd_frequency_case)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
