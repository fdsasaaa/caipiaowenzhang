from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.article_memory import get_article_record
from engine.knowledge_io import iter_brbcw_families
from engine.real_knowledge_multistage import real_knowledge_pipeline_evidence


DEFAULT_ARTICLE_ID = "LCM-IDEA-bf5a9864b004ae17"


def build_preflight(article_id: str = DEFAULT_ARTICLE_ID) -> dict:
    article = get_article_record(article_id)
    if article is None:
        raise LookupError(f"article not found in registry: {article_id}")

    family_id = str(article.get("technique_family") or "")
    family = next((row for row in iter_brbcw_families() if row["f"] == family_id), None)
    if family is None:
        raise LookupError(f"technique family not found in static archive: {family_id}")

    evidence = real_knowledge_pipeline_evidence(article)
    archived_refs = set(family.get("e") or [])
    article_refs = set(article.get("source_refs") or [])
    if not article_refs or not article_refs.intersection(archived_refs):
        raise ValueError("article source_refs do not match the archived real-family provenance")

    return {
        "status": "offline_preflight_pass",
        "article_id": article_id,
        "technique_family": family_id,
        "technique_atoms": article.get("technique_atoms", []),
        "source_refs": article.get("source_refs", []),
        "source_support_count": family.get("n", 0),
        "source_risk_rate": family.get("r", 0.0),
        "rule_refs": article.get("rule_refs", []),
        "subject_lottery": article.get("subject_lottery"),
        "subject_play": article.get("subject_play"),
        **evidence,
        "paid_model_call": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline real-knowledge multistage preflight")
    parser.add_argument("--article-id", default=DEFAULT_ARTICLE_ID)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = build_preflight(args.article_id)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
