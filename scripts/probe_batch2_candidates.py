#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import defaultdict

from engine.planner import plan_articles
from engine.rules import load_rules

rules = [
    r for r in load_rules()
    if r.get("status") == "verified" and r.get("scope", "full") in {"mechanics", "full"}
]

print("=== VERIFIED_MECHANICS ===")
for r in sorted(rules, key=lambda x: (str(x.get("lottery")), str(x.get("play")), str(x.get("rule_id")))):
    print(json.dumps({
        "rule_id": r.get("rule_id"),
        "lottery": r.get("lottery"),
        "play": r.get("play"),
        "aliases": r.get("aliases", []),
        "scope": r.get("scope", "full"),
    }, ensure_ascii=False, sort_keys=True))

pairs = []
seen = set()
for r in rules:
    key = (r.get("lottery"), r.get("play"))
    if not all(key) or key in seen:
        continue
    seen.add(key)
    pairs.append(key)

print("=== SOURCE_BACKED_CANDIDATES ===")
for lottery, play in sorted(pairs):
    result = plan_articles("", lottery, play, 12)
    plans = result.get("plans", [])
    print(json.dumps({
        "lottery": lottery,
        "play": play,
        "status": result.get("status"),
        "rule_refs": result.get("capability", {}).get("mechanics_rule_refs", []),
        "candidate_count": len(plans),
        "candidates": [
            {
                "family": p.get("technique_family"),
                "atoms": p.get("technique_atoms", []),
                "positions": p.get("positions", []),
                "source_refs": p.get("source_refs", []),
                "support": p.get("source_support_count", 0),
                "risk": p.get("source_risk_rate", 0),
                "case_ready": p.get("case_plan", {}).get("case_engine_ready", False),
                "case_supported": p.get("case_plan", {}).get("supported", []),
                "case_unsupported": p.get("case_plan", {}).get("unsupported", []),
            }
            for p in plans
        ],
    }, ensure_ascii=False, sort_keys=True))
