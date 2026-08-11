#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from engine.approval import evaluate_for_approval
from engine.blueprints import blueprint_from_plan
from engine.draft_packets import build_draft_packet
from engine.planner import plan_articles

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / "smoke" / "batch2"
manifest = json.loads((BATCH / "manifest.json").read_text(encoding="utf-8"))

for spec in manifest["articles"]:
    result = plan_articles("", "时时彩", spec["rule_play"], 300)
    matches = [
        p for p in result.get("plans", [])
        if p.get("technique_family") == spec["family_id"]
        and p.get("resolved_selector") == spec["resolved_selector"]
    ]
    if not matches:
        raise SystemExit(f"missing plan for {spec['article_id']}")
    plan = dict(matches[0])
    plan["subject_lottery"] = "分分彩"
    plan["subject_play"] = spec["subject_play"]
    blueprint = blueprint_from_plan(plan)
    packet = build_draft_packet(blueprint)
    article = json.loads((BATCH / "articles" / f"{spec['article_id']}.json").read_text(encoding="utf-8"))
    approval = evaluate_for_approval(packet, article)
    if not approval.approved or approval.publish_package is None:
        raise SystemExit(f"approval failed for {spec['article_id']}: {approval.errors}")
    package = dict(approval.publish_package)
    package["approved_at"] = "2026-08-11T12:45:00+00:00"
    print("PACKAGE=" + json.dumps(package, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
