from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.batch_production_v2 import produce_ranked_batch
from engine.formal_approved_inventory import FormalInventoryError, stage_formal_approved_package
from engine.provider_transport import make_responses_transport, normalize_base_url
from engine.seo_priority import read_demand_signals


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Rank, generate and review a batch of V2 article drafts")
    parser.add_argument("--provider", required=True)
    parser.add_argument("--lottery", required=True)
    parser.add_argument("--play", required=True)
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--signals", type=Path)
    parser.add_argument("--model")
    parser.add_argument("--base-url", default=os.getenv("OPENAI_BASE_URL"), help="OpenAI-compatible base URL ending at /v1")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--record", action="store_true", help="append each review lifecycle result to Registry")
    parser.add_argument(
        "--stage-approved",
        action="store_true",
        help="stage every successful Approved Package into articles/approved; does not sync, schedule or publish",
    )
    args = parser.parse_args()

    signals = read_demand_signals(args.signals)
    transport = make_responses_transport(args.base_url) if args.base_url else None
    result = produce_ranked_batch(
        args.provider,
        args.lottery,
        args.play,
        count=args.count,
        signals=signals,
        model=args.model,
        transport=transport,
        record=args.record,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = dict(result)
    manifest["results"] = []
    manifest["model_base_url"] = normalize_base_url(args.base_url) if args.base_url else "https://api.openai.com/v1"
    manifest["formal_inventory_requested"] = bool(args.stage_approved)
    manifest["formal_inventory_staged"] = 0
    manifest["formal_inventory_unchanged"] = 0
    manifest["formal_inventory_errors"] = []

    for item in result["results"]:
        article_id = str(item.get("article_id") or "unknown")
        folder = args.output_dir / article_id
        folder.mkdir(parents=True, exist_ok=True)
        _write(folder / "blueprint.json", item.get("blueprint") or {})
        _write(folder / "draft_packet.json", item.get("packet") or {})
        if item.get("draft"):
            _write(folder / "draft.json", item["draft"])
        _write(folder / "review.json", {
            "article_id": article_id,
            "status": item.get("status"),
            "approved": item.get("approved"),
            "priority_score": item.get("priority_score"),
            "priority_band": item.get("priority_band"),
            "signal_mode": item.get("signal_mode"),
            "error": item.get("error"),
            "approval": item.get("approval"),
        })

        inventory_result = None
        if item.get("approved_package"):
            _write(folder / "approved.json", item["approved_package"])
            if args.stage_approved:
                try:
                    inventory_result = stage_formal_approved_package(item["approved_package"])
                    if inventory_result["status"] == "staged":
                        manifest["formal_inventory_staged"] += 1
                    elif inventory_result["status"] == "unchanged":
                        manifest["formal_inventory_unchanged"] += 1
                except FormalInventoryError as exc:
                    error = {"article_id": article_id, "error": str(exc)}
                    manifest["formal_inventory_errors"].append(error)
                    inventory_result = {"status": "rejected", "error": str(exc)}

        manifest["results"].append({
            "article_id": article_id,
            "status": item.get("status"),
            "approved": item.get("approved"),
            "folder": str(folder),
            "formal_inventory": inventory_result,
        })

    _write(args.output_dir / "manifest.json", manifest)
    summary = {
        "requested": result["requested"],
        "selected": result["selected"],
        "generated": result["generated"],
        "approved": result["approved"],
        "failed": result["failed"],
        "signal_mode": result["signal_mode"],
        "model_base_url": manifest["model_base_url"],
        "output_dir": str(args.output_dir),
        "formal_inventory_requested": bool(args.stage_approved),
        "formal_inventory_staged": manifest["formal_inventory_staged"],
        "formal_inventory_unchanged": manifest["formal_inventory_unchanged"],
        "formal_inventory_error_count": len(manifest["formal_inventory_errors"]),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if manifest["formal_inventory_errors"]:
        return 7
    return 0 if result["approved"] > 0 else 6


if __name__ == "__main__":
    raise SystemExit(main())
