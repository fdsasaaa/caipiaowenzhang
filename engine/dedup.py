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


NON_OWNING_REJECTED_STATUSES = {
    "rejected",
    "rejected_for_revision",
    "approval_failed",
}


def _text(value) -> str:
    return "" if value is None else str(value)


def _atoms(value) -> str:
    if not value:
        return ""
    return " ".join(_text(item) for item in value if item is not None)


def _subject(record: dict, subject_key: str, rule_key: str) -> str:
    value = record.get(subject_key)
    return _text(value if value not in (None, "") else record.get(rule_key))


def _core(record: dict) -> str:
    return "|".join([
        _text(record.get("title")),
        _text(record.get("primary_keyword")),
        _text(record.get("search_intent")),
        _subject(record, "subject_lottery", "lottery"),
        _subject(record, "subject_play", "play"),
        _atoms(record.get("technique_atoms")),
        _text(record.get("case_structure")),
    ])


def duplicate_candidates(candidate: dict, threshold: float = 0.72) -> list[DuplicateHit]:
    hits: list[DuplicateHit] = []
    candidate_article_id = candidate.get("article_id")
    candidate_core = _core(candidate)
    for old in iter_registry("articles"):
        # Explicit rejected/revision-only rows are historical attempts, not live
        # content owners. Statusless legacy rows remain owners for backward
        # compatibility, as do all non-rejected lifecycle states.
        if str(old.get("status") or "") in NON_OWNING_REJECTED_STATUSES:
            continue
        old_article_id = old.get("article_id")
        # Lifecycle updates of the same article are not duplicates of themselves.
        if candidate_article_id and old_article_id == candidate_article_id:
            continue
        if candidate.get("fingerprint") and candidate.get("fingerprint") == old.get("fingerprint"):
            hits.append(DuplicateHit(_text(old_article_id), _text(old.get("title")), 1.0, "same fingerprint"))
            continue
        old_core = _core(old)
        score = jaccard(candidate_core, old_core)
        if score >= threshold:
            hits.append(DuplicateHit(_text(old_article_id), _text(old.get("title")), score, "lexical/core overlap"))
    return sorted(hits, key=lambda x: x.score, reverse=True)
