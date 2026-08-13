from __future__ import annotations

import re
from dataclasses import dataclass

from .article_angles import AUDITED_ANGLE_STRUCTURAL_WEIGHT, same_audited_angle
from .store import iter_registry

STRUCTURAL_DUPLICATE_THRESHOLD = 0.82


@dataclass
class StructuralDuplicateHit:
    article_id: str
    title: str
    score: float
    reasons: list[str]


NON_OWNING_REJECTED_STATUSES = {
    "rejected",
    "rejected_for_revision",
    "approval_failed",
}


def _set(value) -> set[str]:
    if not value:
        return set()
    if isinstance(value, str):
        return {x for x in re.split(r"[,|/+\s]+", value) if x}
    return {str(x) for x in value if x not in (None, "")}


def _jaccard(a: set[str], b: set[str]) -> float:
    # Missing structure is absence of evidence, not evidence of similarity.
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _subject(record: dict, subject_key: str, rule_key: str) -> str:
    return str(record.get(subject_key) or record.get(rule_key) or "").strip()


def play_family(play: str) -> str:
    value = str(play or "")
    if "定位胆" in value or value in {"一星", "万位", "千位", "百位", "十位", "个位"}:
        return "定位胆"
    window = next((x for x in ("前二", "后二", "前三", "中三", "后三", "前四", "后四", "五星") if x in value), "")
    if "组选" in value or "组三" in value or "组六" in value:
        kind = "组选"
    elif "直选" in value:
        kind = "直选"
    elif "大小单双" in value:
        kind = "大小单双"
    else:
        kind = value
    return f"{window}:{kind}" if window else kind


def _case_parts(record: dict) -> tuple[str, set[str]]:
    structure = str(record.get("case_structure") or "")
    selector = ""
    metrics: set[str] = set()
    for part in structure.split(";"):
        key, _, value = part.partition("=")
        if key == "selector":
            selector = value.strip()
        elif key == "metrics":
            metrics = _set(value)
    return selector, metrics


def structural_similarity(candidate: dict, old: dict) -> tuple[float, list[str]]:
    reasons: list[str] = []
    score = 0.0

    cand_lottery = _subject(candidate, "subject_lottery", "lottery")
    old_lottery = _subject(old, "subject_lottery", "lottery")
    if cand_lottery and cand_lottery == old_lottery:
        score += 0.10; reasons.append("same_subject_lottery")

    cand_family = play_family(_subject(candidate, "subject_play", "play"))
    old_family = play_family(_subject(old, "subject_play", "play"))
    if cand_family and cand_family == old_family:
        score += 0.20; reasons.append("same_play_family")

    cand_atoms, old_atoms = _set(candidate.get("technique_atoms")), _set(old.get("technique_atoms"))
    atom_sim = _jaccard(cand_atoms, old_atoms)
    score += 0.35 * atom_sim
    if atom_sim >= 0.75:
        reasons.append(f"technique_atoms={atom_sim:.2f}")

    cand_selector, cand_metrics = _case_parts(candidate)
    old_selector, old_metrics = _case_parts(old)
    if cand_selector and cand_selector == old_selector:
        score += 0.15; reasons.append("same_case_selector")
    metric_sim = _jaccard(cand_metrics, old_metrics)
    score += 0.15 * metric_sim
    if metric_sim >= 0.75:
        reasons.append(f"case_metrics={metric_sim:.2f}")

    cand_type, old_type = str(candidate.get("content_type") or ""), str(old.get("content_type") or "")
    if cand_type and cand_type == old_type:
        score += 0.05; reasons.append("same_content_type")

    base_score = min(1.0, score)
    same_angle = same_audited_angle(candidate, old)
    if same_angle is None:
        return base_score, reasons
    weight = AUDITED_ANGLE_STRUCTURAL_WEIGHT
    if same_angle:
        reasons.append("same_audited_information_gain")
        return min(1.0, (1.0 - weight) * base_score + weight), reasons
    reasons.append("different_audited_information_gain")
    return min(1.0, (1.0 - weight) * base_score), reasons


def structural_duplicate_candidates(
    candidate: dict, threshold: float = STRUCTURAL_DUPLICATE_THRESHOLD
) -> list[StructuralDuplicateHit]:
    article_id = candidate.get("article_id")
    hits: list[StructuralDuplicateHit] = []
    for old in iter_registry("articles"):
        # Explicit rejected/revision-only rows are historical attempts, not live
        # structural owners. Statusless legacy rows remain owners for backward
        # compatibility, as do all non-rejected lifecycle states.
        if str(old.get("status") or "") in NON_OWNING_REJECTED_STATUSES:
            continue
        if article_id and old.get("article_id") == article_id:
            continue
        if candidate.get("fingerprint") and candidate.get("fingerprint") == old.get("fingerprint"):
            hits.append(StructuralDuplicateHit(str(old.get("article_id") or ""), str(old.get("title") or ""), 1.0, ["same_fingerprint"]))
            continue
        score, reasons = structural_similarity(candidate, old)
        if score >= threshold:
            hits.append(StructuralDuplicateHit(str(old.get("article_id") or ""), str(old.get("title") or ""), score, reasons))
    return sorted(hits, key=lambda h: h.score, reverse=True)
