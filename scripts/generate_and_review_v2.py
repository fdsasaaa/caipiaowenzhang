from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.ai_generation import GenerationError, generate_article
from engine.approval import evaluate_and_record, evaluate_for_approval
from engine.formal_approved_inventory import FormalInventoryError, stage_formal_approved_package


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a constrained article draft and run the normal Approval Pipeline")
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--draft-output", required=True, type=Path)
    parser.add_argument("--report-output", required=True, type=Path)
    parser.add_argument("--approved-output", type=Path)
    parser.add_argument("--model")
    parser.add_argument("--record", action="store_true", help="append lifecycle state to Registry after review")
    parser.add_argument(
        "--stage-approved",
        action="store_true",
        help="after Approval succeeds, atomically stage the Approved Package into articles/approved; does not sync or publish",
    )
    args = parser.parse_args()

    packet = json.loads(args.packet.read_text(encoding="utf-8"))
    try:
        generated = generate_article(packet, model=args.model)
    except GenerationError as exc:
        report = {"generated": False, "approved": False, "error": str(exc)}
        _write(args.report_output, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 8

    article = generated.article
    _write(args.draft_output, article)
    approval = evaluate_and_record(packet, article) if args.record else evaluate_for_approval(packet, article)
    report = {
        "generated": True,
        "provider": generated.provider,
        "model": generated.model,
        "response_id": generated.response_id,
        "approved": approval.approved,
        "status": approval.status,
        "quality_score": approval.quality_score,
        "errors": approval.errors,
        "warnings": approval.warnings,
        "draft_output": str(args.draft_output),
        "registry_record": approval.registry_record,
        "formal_inventory_requested": bool(args.stage_approved),
    }
    if approval.approved and approval.publish_package and args.approved_output:
        _write(args.approved_output, approval.publish_package)
        report["approved_output"] = str(args.approved_output)

    if approval.approved and approval.publish_package and args.stage_approved:
        try:
            report["formal_inventory"] = stage_formal_approved_package(approval.publish_package)
        except FormalInventoryError as exc:
            report["formal_inventory_error"] = str(exc)
            _write(args.report_output, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 7

    _write(args.report_output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if approval.approved else 6


if __name__ == "__main__":
    raise SystemExit(main())
