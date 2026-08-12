from __future__ import annotations

from collections import defaultdict

from .store import iter_registry

ACTIVE_ARTICLE_STATUSES = {
    "idea",
    "draft",
    "approved",
    "queued",
    "scheduled",
    "published",
}

# Canonical reader-facing method labels, ordered for stable SEO ownership.
# position_filter is deliberately omitted because it describes calculation
# scope, not a useful standalone search modifier.
#
# V1.4 keeps single-method keywords backward-natural (e.g. 分分时时彩后三和值技巧)
# but allows up to three distinct method labels for genuinely composite
# articles (e.g. 分分时时彩后三和值跨度奇偶技巧). This prevents structurally
# different method articles from being collapsed onto one exact primary owner.
ATOM_KEYWORD_MODIFIERS = (
    ("cold_hot_split", "冷热"),
    ("omission_threshold", "遗漏"),
    ("sum_range", "和值"),
    ("span_range", "跨度"),
    ("frequency_window", "频率"),
    ("repeat_number", "重号"),
    ("neighbor_number", "邻号"),
    ("consecutive_number", "连号"),
    ("dan_candidate", "胆码"),
    ("kill_candidate", "杀号"),
    ("compound_selection", "复式"),
    ("big_small_filter", "大小"),
    ("odd_even_filter", "奇偶"),
    ("group3_group6", "组三组六"),
)

MAX_PRIMARY_KEYWORD_METHOD_LABELS = 3

# Some play names use the market's natural vocabulary instead of the internal
# atom label. `大小单双` already expresses both big/small and odd/even, so
# appending `奇偶` would be redundant and would also rewrite accepted historical
# smoke artifacts for no information gain.
PLAY_EMBEDDED_METHOD_ATOMS = (
    ("大小单双", {"big_small_filter", "odd_even_filter"}),
)


def normalize_keyword(value: object) -> str:
    return "".join(str(value or "").split()).casefold()


def _play_already_expresses_atom(play: str, atom: str, label: str) -> bool:
    if label and label in play:
        return True
    for marker, atoms in PLAY_EMBEDDED_METHOD_ATOMS:
        if marker in play and atom in atoms:
            return True
    return False


def method_keyword_labels(play: str, atoms: list[str] | tuple[str, ...] | None = None) -> list[str]:
    """Return stable, reader-facing SEO labels for the article's real method atoms.

    Labels already explicit or semantically embedded in the play name are omitted
    to avoid awkward repetition. The result is deterministic and independent of
    source atom order.
    """
    play = str(play or "").strip()
    atom_set = set(atoms or [])
    labels: list[str] = []
    for atom, label in ATOM_KEYWORD_MODIFIERS:
        if atom not in atom_set:
            continue
        if _play_already_expresses_atom(play, atom, label):
            continue
        if label not in labels:
            labels.append(label)
    return labels


def primary_keyword_for(lottery: str, play: str, atoms: list[str] | tuple[str, ...] | None = None) -> str:
    lottery = str(lottery or "").strip()
    play = str(play or "").strip()
    labels = method_keyword_labels(play, atoms)[:MAX_PRIMARY_KEYWORD_METHOD_LABELS]
    modifier = "".join(labels)
    return f"{lottery}{play}{modifier}技巧"


def canonical_primary_keyword(record: dict) -> str:
    """Return the effective exact-match SEO owner key for an article record.

    V1.4 derives method-article keywords from subject + up to three canonical
    technique labels. This intentionally lets legacy registry rows keep their
    historical metadata while ownership/audit uses the current canonical rule.
    """
    if record.get("information_gain_type") == "method_mechanics_and_reproducible_case":
        lottery = record.get("subject_lottery") or record.get("lottery") or ""
        play = record.get("subject_play") or record.get("play") or ""
        if lottery and play:
            return primary_keyword_for(str(lottery), str(play), record.get("technique_atoms") or [])
    return str(record.get("primary_keyword") or "").strip()


def keyword_owners(primary_keyword: str, exclude_article_id: str | None = None) -> list[dict]:
    target = normalize_keyword(primary_keyword)
    if not target:
        return []
    owners: list[dict] = []
    for row in iter_registry("articles"):
        article_id = row.get("article_id")
        if exclude_article_id and article_id == exclude_article_id:
            continue
        if row.get("status") not in ACTIVE_ARTICLE_STATUSES:
            continue
        if normalize_keyword(canonical_primary_keyword(row)) == target:
            owners.append(row)
    return owners


def keyword_ownership_conflicts() -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    display: dict[str, str] = {}
    for row in iter_registry("articles"):
        if row.get("status") not in ACTIVE_ARTICLE_STATUSES:
            continue
        keyword = canonical_primary_keyword(row)
        normalized = normalize_keyword(keyword)
        if not normalized:
            continue
        grouped[normalized].append(row)
        display.setdefault(normalized, keyword)

    conflicts = []
    for normalized, rows in grouped.items():
        article_ids = sorted({str(r.get("article_id") or "") for r in rows if r.get("article_id")})
        if len(article_ids) <= 1:
            continue
        conflicts.append({
            "primary_keyword": display[normalized],
            "article_ids": article_ids,
        })
    return sorted(conflicts, key=lambda x: normalize_keyword(x["primary_keyword"]))
