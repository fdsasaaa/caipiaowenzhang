from __future__ import annotations

from datetime import datetime, timezone

from .quality import evaluate
from .store import append_jsonl
from .text import fingerprint, sha256_text


def prepare_article(article: dict) -> dict:
    row = dict(article)
    row.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    row["content_hash"] = sha256_text(row.get("content", ""))
    row["fingerprint"] = fingerprint(
        row.get("primary_keyword", ""), row.get("search_intent", ""), row.get("lottery", ""),
        row.get("play", ""), " ".join(row.get("technique_atoms", [])), row.get("case_structure", ""),
    )
    return row


def register_article(article: dict, require_pass: bool = True) -> tuple[dict, object]:
    row = prepare_article(article)
    report = evaluate(row)
    if require_pass and not report.passed:
        raise ValueError({"score": report.score, "errors": report.errors, "warnings": report.warnings})
    append_jsonl("articles", row)
    return row, report
