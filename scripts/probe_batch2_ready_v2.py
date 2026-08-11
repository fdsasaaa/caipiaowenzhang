#!/usr/bin/env python3
from __future__ import annotations

import json

from engine.planner import plan_articles

TARGETS = {
    "FAM-32137acbb90340b9": ("时时彩", "后二大小单双"),
    "FAM-66e3a5bb1e229e8a": ("时时彩", "定位胆"),
    "FAM-c9d752aac7c51169": ("时时彩", "后三组选3"),
    "FAM-c93cfcc1527bf6f8": ("时时彩", "后三直选"),
    "FAM-bee5958fb0d2f766": ("时时彩", "定位胆"),
}

for family_id, (lottery, play) in TARGETS.items():
    result = plan_articles("", lottery, play, 300)
    matches = [p for p in result.get("plans", []) if p.get("technique_family") == family_id]
    print(json.dumps({
        "family_id": family_id,
        "lottery": lottery,
        "play": play,
        "planner_status": result.get("status"),
        "matches": [
            {
                "atoms": p.get("technique_atoms", []),
                "source_positions": p.get("positions", []),
                "resolved_selector": p.get("resolved_selector"),
                "selector_basis": p.get("selector_basis"),
                "source_refs": p.get("source_refs", []),
                "source_support_count": p.get("source_support_count"),
                "source_risk_rate": p.get("source_risk_rate"),
                "case_engine_ready": p.get("case_plan", {}).get("case_engine_ready"),
                "case_supported": p.get("case_plan", {}).get("supported", []),
                "case_unsupported": p.get("case_plan", {}).get("unsupported", []),
            }
            for p in matches
        ],
    }, ensure_ascii=False, sort_keys=True))

    if not matches:
        raise SystemExit(f"target family not found: {family_id} for {play}")
    if not any(p.get("case_plan", {}).get("case_engine_ready") for p in matches):
        raise SystemExit(f"target family not case-ready: {family_id} for {play}")
