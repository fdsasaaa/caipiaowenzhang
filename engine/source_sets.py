from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SETS = ROOT / "knowledge" / "source_sets"


def brbcw_selected_ids() -> list[int]:
    text = "".join(p.read_text(encoding="ascii") for p in sorted(SOURCE_SETS.glob("brbcw_selected_ids.part-*.txt")))
    if not text.strip():
        return []
    return [int(x) for x in text.split(",") if x.strip()]


def iter_brbcw_sources():
    for thread_id in brbcw_selected_ids():
        yield {
            "source_id": f"BRBCW-{thread_id:06d}",
            "source_type": "forum_article_reference",
            "source_name": "brbcw.com",
            "thread_id": thread_id,
            "url": f"https://brbcw.com/thread-{thread_id}-1-1.html",
            "claim_status": "unverified",
            "usage": "idea_and_case_source_only",
        }
