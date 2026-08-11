from __future__ import annotations

import argparse
import json
from pathlib import Path

from .approval import evaluate_and_record, evaluate_for_approval
from .article_memory import reserve_blueprints
from .blueprints import generate_blueprints
from .casebook import descriptive_case, frequency_case, omission_case
from .compliance import validate_portfolio
from .draft_packets import generate_draft_packets
from .format_rules import validate_format
from .internal_links import audit_internal_link_plan, plan_all_internal_links, plan_internal_links
from .link_revision import build_internal_link_revision
from .planner import plan_articles
from .rule_gaps import list_gaps, record_gap
from .rules import load_rules, rule_capability
from .seo_keywords import keyword_ownership_conflicts
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
    keyword_conflicts = keyword_ownership_conflicts()
    for conflict in keyword_conflicts:
        problems.append(
            "exact primary keyword has multiple active owners: "
            + conflict["primary_keyword"]
            + " -> "
            + ",".join(conflict["article_ids"])
        )
    result = {
        "ok": not problems,
        "problems": problems,
        "registry": counts(),
        "rule_gaps": len(list_gaps()),
        "keyword_conflicts": len(keyword_conflicts),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not problems else 2


def cmd_plan(args: argparse.Namespace) -> int:
    result = plan_articles(args.provider, args.lottery, args.play, args.count)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked_mechanics_verification" else 3


def cmd_blueprints(args: argparse.Namespace) -> int:
    result = generate_blueprints(args.provider, args.lottery, args.play, args.count)
    if args.reserve:
        result["reservation"] = reserve_blueprints(result["blueprints"])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ready"] > 0 else 3


def cmd_draft_packets(args: argparse.Namespace) -> int:
    result = generate_draft_packets(args.provider, args.lottery, args.play, args.count)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["generated"] > 0 else 3


def cmd_approve_draft(args: argparse.Namespace) -> int:
    packet = json.loads(Path(args.packet).read_text(encoding="utf-8"))
    article = json.loads(Path(args.article).read_text(encoding="utf-8"))
    result = evaluate_and_record(packet, article) if args.record else evaluate_for_approval(packet, article)
    payload = {
        "approved": result.approved,
        "status": result.status,
        "quality_score": result.quality_score,
        "errors": result.errors,
        "warnings": result.warnings,
        "registry_record": result.registry_record,
        "publish_package": result.publish_package,
    }
    if args.output and result.publish_package:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result.publish_package, ensure_ascii=False, indent=2), encoding="utf-8")
        payload["written_to"] = str(out)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if result.approved else 6


def cmd_internal_links(args: argparse.Namespace) -> int:
    result = plan_internal_links(args.article_id, limit=args.limit, min_score=args.min_score)
    result["audit_errors"] = audit_internal_link_plan(result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "planned" and not result["audit_errors"] else 7


def cmd_internal_links_all(args: argparse.Namespace) -> int:
    result = plan_all_internal_links(limit=args.limit, min_score=args.min_score)
    errors = []
    for plan in result["plans"]:
        for error in audit_internal_link_plan(plan):
            errors.append(f"{plan.get('article_id')}: {error}")
    result["audit_errors"] = errors
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 7


def cmd_internal_link_revision(args: argparse.Namespace) -> int:
    package = json.loads(Path(args.package).read_text(encoding="utf-8"))
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    revision = build_internal_link_revision(package, plan, max_links=args.max_links)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(revision, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": "draft_revision_created",
        "article_id": revision.get("article_id"),
        "revision_reason": revision.get("revision_reason"),
        "revision_of_content_hash": revision.get("revision_of_content_hash"),
        "proposed_content_hash": revision.get("proposed_content_hash"),
        "links": len(revision.get("internal_links", [])),
        "written_to": str(out),
        "requires_reapproval": True,
    }, ensure_ascii=False, indent=2))
    return 0


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


def cmd_validate_format(args: argparse.Namespace) -> int:
    report = validate_format(args.play_type, args.play_name, args.content)
    print(json.dumps(report.__dict__, ensure_ascii=False, indent=2))
    return 0 if report.passed else 4


def cmd_check_portfolio(args: argparse.Namespace) -> int:
    payload = json.loads(Path(args.file).read_text(encoding="utf-8"))
    bets = payload.get("bets", []) if isinstance(payload, dict) else payload
    if not isinstance(bets, list):
        raise ValueError("portfolio JSON must be a list or an object with a bets list")
    report = validate_portfolio(bets)
    print(json.dumps({"passed": report.passed, "violations": report.violations, "groups": report.groups}, ensure_ascii=False, indent=2))
    return 0 if report.passed else 5


def _add_draw_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--draw", action="append", required=True, help="chronological draw, oldest to newest; repeat option")


def _add_article_scope_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--provider", required=True)
    p.add_argument("--lottery", required=True)
    p.add_argument("--play", required=True)
    p.add_argument("--count", type=int, default=10)


def _add_link_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--limit", type=int, default=3)
    p.add_argument("--min-score", type=int, default=45)


def main() -> int:
    parser = argparse.ArgumentParser(prog="laocaimi-content-engine")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, fn in (("init", cmd_init), ("status", cmd_status), ("rebuild", cmd_rebuild), ("audit", cmd_audit), ("rule-gaps", cmd_rule_gaps)):
        p = sub.add_parser(name)
        p.set_defaults(func=fn)
    p = sub.add_parser("plan")
    _add_article_scope_args(p)
    p.set_defaults(func=cmd_plan)
    p = sub.add_parser("blueprints")
    _add_article_scope_args(p)
    p.add_argument("--reserve", action="store_true", help="persist ready non-duplicate angles as idea records")
    p.set_defaults(func=cmd_blueprints)
    p = sub.add_parser("draft-packets")
    _add_article_scope_args(p)
    p.set_defaults(func=cmd_draft_packets)
    p = sub.add_parser("approve-draft")
    p.add_argument("--packet", required=True, help="Draft Packet JSON path")
    p.add_argument("--article", required=True, help="AI draft article JSON path")
    p.add_argument("--output", help="write Approved Package JSON here when approved")
    p.add_argument("--record", action="store_true", help="append approved/rejected lifecycle state to article registry")
    p.set_defaults(func=cmd_approve_draft)
    p = sub.add_parser("internal-links")
    p.add_argument("--article-id", required=True)
    _add_link_args(p)
    p.set_defaults(func=cmd_internal_links)
    p = sub.add_parser("internal-links-all")
    _add_link_args(p)
    p.set_defaults(func=cmd_internal_links_all)
    p = sub.add_parser("internal-link-revision")
    p.add_argument("--package", required=True, help="approved package JSON path")
    p.add_argument("--plan", required=True, help="resolved internal link plan JSON path")
    p.add_argument("--output", required=True, help="write draft revision JSON here")
    p.add_argument("--max-links", type=int, default=3)
    p.set_defaults(func=cmd_internal_link_revision)
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
    p = sub.add_parser("validate-format")
    p.add_argument("--play-type", required=True)
    p.add_argument("--play-name", required=True)
    p.add_argument("--content", required=True)
    p.set_defaults(func=cmd_validate_format)
    p = sub.add_parser("check-portfolio")
    p.add_argument("--file", required=True, help="JSON list of normalized bets, or object with bets list")
    p.set_defaults(func=cmd_check_portfolio)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
