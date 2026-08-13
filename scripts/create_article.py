from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.article_memory import append_article_state
from engine.creator_first import (
    CreatorFirstError,
    build_creator_prompt,
    build_creator_request,
    generate_creator_article,
)
from engine.formal_approved_inventory import FormalInventoryError, stage_formal_approved_package
from engine.provider_transport import make_responses_transport, normalize_base_url


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Creator-first: AI freely creates one article; existing systems only validate and remember it."
    )
    parser.add_argument("--request-id", help="optional deterministic request id for audit/testing")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL") or "gpt-5.4-mini")
    parser.add_argument("--execute", action="store_true", help="make exactly one model request; there is no automatic retry")
    parser.add_argument("--stage-formal", action="store_true", help="stage an approved package and append approved Registry lifecycle")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    request = build_creator_request(request_id=args.request_id)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir or Path("runs") / f"creator-first-{stamp}"
    _write(output_dir / "request.json", request)

    if not args.execute:
        summary = {
            "status": "CREATOR_READY",
            "mode": "creator_first",
            "article_id": request["article_id"],
            "verified_mechanics_available": len(request["available_mechanics"]),
            "memory_articles_supplied": len(request["existing_article_memory"]),
            "automatic_retry": False,
            "planner_used": False,
            "angle_contract_used": False,
            "candidate_capacity_required": False,
            "provider_call": False,
            "website_sync": False,
            "scheduled": False,
            "published": False,
        }
        _write(output_dir / "summary.json", summary)
        _write(output_dir / "prompt.json", {"prompt": build_creator_prompt(request)})
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print(json.dumps({"status": "BLOCKED", "error": "OPENAI_API_KEY missing"}, ensure_ascii=False))
        return 2
    base_url = normalize_base_url(os.getenv("OPENAI_BASE_URL"))
    transport = make_responses_transport(base_url)

    try:
        result = generate_creator_article(
            request,
            model=args.model,
            api_key=api_key,
            transport=transport,
            timeout=300,
        )
    except CreatorFirstError as exc:
        _write(output_dir / "summary.json", {
            "status": "CREATOR_BLOCKED",
            "error": str(exc),
            "provider_requests": 1,
            "automatic_retry": False,
        })
        print(json.dumps({"status": "CREATOR_BLOCKED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 6

    report = {
        "status": "APPROVED" if result.approved else "REJECTED",
        "article_id": result.article.get("article_id"),
        "title": result.article.get("title"),
        "primary_keyword": result.article.get("primary_keyword"),
        "creation_mode": result.manifest.get("creation_mode"),
        "technique_name": result.manifest.get("technique_name"),
        "response_id": result.response_id,
        "quality_score": result.approval.quality_score,
        "editorial_score": result.approval.editorial_score,
        "style_passed": result.style.passed,
        "errors": result.errors,
        "warnings": result.warnings,
        "provider_requests": 1,
        "automatic_retry": False,
        "planner_used": False,
        "angle_contract_used": False,
        "candidate_capacity_required": False,
        "website_sync": False,
        "scheduled": False,
        "published": False,
    }
    _write(output_dir / "manifest.json", result.manifest)
    _write(output_dir / "article.json", result.article)
    _write(output_dir / "packet.json", result.packet)
    _write(output_dir / "review.json", report)

    if args.stage_formal:
        if not result.approved or not result.approval.publish_package or not result.approval.registry_record:
            report["formal_inventory"] = "not_staged"
            report["formal_inventory_reason"] = "article did not pass all creator-first + existing hard gates"
        else:
            try:
                staged = stage_formal_approved_package(result.approval.publish_package)
            except FormalInventoryError as exc:
                report["formal_inventory"] = "error"
                report["formal_inventory_reason"] = str(exc)
                _write(output_dir / "review.json", report)
                print(json.dumps(report, ensure_ascii=False, indent=2))
                return 7
            append_article_state(
                result.article["article_id"],
                "approved",
                result.approval.registry_record,
            )
            report["formal_inventory"] = staged["status"]
            report["formal_inventory_path"] = staged["path"]
        _write(output_dir / "review.json", report)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if result.approved else 6


if __name__ == "__main__":
    raise SystemExit(main())
