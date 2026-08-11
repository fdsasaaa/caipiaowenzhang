from __future__ import annotations

import argparse
import json

from .rules import load_rules
from .store import counts, ensure_layout, rebuild_index


def cmd_init(_: argparse.Namespace) -> int:
    ensure_layout()
    result = rebuild_index()
    print(json.dumps({"initialized": True, "index": result}, ensure_ascii=False, indent=2))
    return 0


def cmd_status(_: argparse.Namespace) -> int:
    print(json.dumps({"registries": counts(), "rules": len(load_rules())}, ensure_ascii=False, indent=2))
    return 0


def cmd_rebuild(_: argparse.Namespace) -> int:
    print(json.dumps(rebuild_index(), ensure_ascii=False, indent=2))
    return 0


def cmd_audit(_: argparse.Namespace) -> int:
    problems = []
    for rule in load_rules():
        for field in ("rule_id", "lottery", "play", "status", "source"):
            if field not in rule:
                problems.append(f"rule missing {field}: {rule}")
        if rule.get("status") == "verified" and not rule.get("verified_at"):
            problems.append(f"verified rule missing verified_at: {rule.get('rule_id')}")
    result = {"ok": not problems, "problems": problems, "registry": counts()}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not problems else 2


def main() -> int:
    parser = argparse.ArgumentParser(prog="laocaimi-content-engine")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, fn in (("init", cmd_init), ("status", cmd_status), ("rebuild", cmd_rebuild), ("audit", cmd_audit)):
        p = sub.add_parser(name)
        p.set_defaults(func=fn)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
