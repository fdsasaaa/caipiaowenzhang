from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .article_memory import append_article_state
from .creator_first import CreatorFirstError, build_creator_prompt
from .creator_quality import build_quality_creator_request, generate_quality_creator_article
from .formal_approved_inventory import FormalInventoryError, stage_formal_approved_package
from .provider_transport import make_responses_transport, normalize_base_url


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Creator-first quality-memory article creation")
    parser.add_argument("--request-id")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL") or "gpt-5.4-mini")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--stage-formal", action="store_true")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)

    request = build_quality_creator_request(request_id=args.request_id)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir or Path("runs") / f"creator-first-{stamp}"
    _write(output_dir / "request.json", request)

    if not args.execute:
        summary = {
            "status": "CREATOR_READY",
            "mode": "creator_first_quality_memory",
            "article_id": request["article_id"],
            "verified_mechanics_available": len(request["available_mechanics"]),
            "recent_registry_memory_articles": len(request["existing_article_memory"]),
            "long_term_formal_memory_articles": (request.get("long_term_memory") or {}).get("article_count", 0),
            "style_dna": (request.get("style_dna") or {}).get("id"),
            "title_candidates_internal": (request.get("title_selection") or {}).get("internal_candidate_count"),
            "automatic_retry": False,
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

    try:
        result = generate_quality_creator_article(
            request,
            model=args.model,
            api_key=api_key,
            transport=make_responses_transport(normalize_base_url(os.getenv("OPENAI_BASE_URL"))),
            timeout=300,
        )
    except CreatorFirstError as exc:
        print(json.dumps({"status": "CREATOR_BLOCKED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 6

    report = {
        "status": "APPROVED" if result.approved else "REJECTED",
        "article_id": result.article.get("article_id"),
        "title": result.article.get("title"),
        "primary_keyword": result.article.get("primary_keyword"),
        "technique_name": result.manifest.get("technique_name"),
        "style_dna": (result.request.get("style_dna") or {}).get("id"),
        "long_term_memory_articles": (result.request.get("long_term_memory") or {}).get("article_count", 0),
        "quality_score": result.approval.quality_score,
        "editorial_score": result.approval.editorial_score,
        "style_passed": result.style.passed,
        "errors": result.errors,
        "warnings": result.warnings,
        "provider_requests": 1,
        "automatic_retry": False,
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
        else:
            try:
                staged = stage_formal_approved_package(result.approval.publish_package)
            except FormalInventoryError as exc:
                report["formal_inventory"] = "error"
                report["formal_inventory_reason"] = str(exc)
                _write(output_dir / "review.json", report)
                print(json.dumps(report, ensure_ascii=False, indent=2))
                return 7
            append_article_state(result.article["article_id"], "approved", result.approval.registry_record)
            report["formal_inventory"] = staged["status"]
            report["formal_inventory_path"] = staged["path"]
            _write(output_dir / "review.json", report)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if result.approved else 6
