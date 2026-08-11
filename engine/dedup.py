from __future__ import annotations

from dataclasses import dataclass

from .store import iter_registry
from .text import jaccard


@dataclass
class DuplicateHit:
    article_id: str
    title: str
    score: float
    reason: str


def duplicate_candidates(candidate: dict, threshold: float = 0.72) -> list[DuplicateHit]:
    hits: list[DuplicateHit] = []
    candidate_article_id = candidate.get("article_id")
    candidate_core = "|".join([
        candidate.get("title", ""),
        candidate.get("primary_keyword", ""),
        candidate.get("search_intent", ""),
        candidate.get("lottery", ""),
        candidate.get("play", ""),
        " ".join(candidate.get("technique_atoms", [])),
        candidate.get("case_structure", ""),
    ])
    for old in iter_registry("articles"):
        old_article_id = old.get("article_id")
        # Lifecycle updates of the same article are not duplicates of themselves.
        if candidate_article_id and old_article_id == candidate_article_id:
            continue
        if candidate.get("fingerprint") and candidate.get("fingerprint") == old.get("fingerprint"):
            hits.append(DuplicateHit(old_article_id or "", old.get("title", ""), 1.0, "same fingerprint"))
            continue
        old_core = "|".join([
            old.get("title", ""), old.get("primary_keyword", ""), old.get("search_intent", ""),
            old.get("lottery", ""), old.get("play", ""), " ".join(old.get("technique_atoms", [])),
            old.get("case_structure", ""),
        ])
        score = jaccard(candidate_core, old_core)
        if score >= threshold:
            hits.append(DuplicateHit(old_article_id or "", old.get("title", ""), score, "lexical/core overlap"))
    return sorted(hits, key=lambda x: x.score, reverse=True)
