from __future__ import annotations

import json
from pathlib import Path

from .analysis_metrics import POSITION_INDEX, WINDOW_INDEXES

ROOT = Path(__file__).resolve().parents[1]
SEMANTICS_FILE = ROOT / "knowledge" / "TECHNIQUE_SEMANTICS.json"

CANONICAL_POSITIONS = tuple(POSITION_INDEX)
CANONICAL_WINDOWS = tuple(WINDOW_INDEXES)


def load_semantics() -> dict:
    return json.loads(SEMANTICS_FILE.read_text(encoding="utf-8"))


def fixed_selector_for_play(play: str) -> str | None:
    """Resolve the mathematical selector implied by a verified play name."""
    play = str(play or "")
    # More specific windows first. Group/direct suffixes do not change the position window.
    for selector in ("前二", "后二", "前三", "中三", "后三", "前四", "后四", "五星"):
        if selector in play:
            return selector
    if "一星" in play:
        return "个位"
    for selector in CANONICAL_POSITIONS:
        if selector in play:
            return selector
    return None


def selector_variants(play: str, source_positions: list[str] | None, atoms: list[str]) -> list[dict]:
    """Return explicit case selectors with provenance.

    A fixed-window play (e.g. 后三直选) always wins over source-list ordering.
    If a family explicitly contains position_filter, its source position metadata
    must support the fixed selector. For generic 定位胆, each source-supported
    single position becomes a separate variant. If a non-position-filter family
    targets 定位胆 without source positions, 个位 is used only as an explicit
    reproducible example selector, not as a prediction claim.
    """
    positions = [str(x) for x in (source_positions or []) if str(x)]
    has_position_filter = "position_filter" in atoms
    fixed = fixed_selector_for_play(play)
    if fixed:
        if has_position_filter and positions and fixed not in positions:
            return []
        return [{
            "selector": fixed,
            "basis": "verified_play",
            "source_position_supported": (not positions) or fixed in positions,
        }]

    if str(play or "") == "定位胆":
        singles = [p for p in CANONICAL_POSITIONS if p in positions]
        if has_position_filter:
            return [
                {"selector": p, "basis": "source_position", "source_position_supported": True}
                for p in singles
            ]
        if singles:
            return [
                {"selector": p, "basis": "source_position", "source_position_supported": True}
                for p in singles
            ]
        # The verified 定位胆 mechanics allow a single-position example. Choosing 个位
        # here is a deterministic case default and is surfaced in case_plan.
        return [{
            "selector": "个位",
            "basis": "deterministic_example_default",
            "source_position_supported": False,
        }]

    return []


def case_requirements(atoms: list[str], selector: str | None = None, selector_basis: str | None = None) -> dict:
    definitions = load_semantics().get("atoms", {})
    supported = []
    unsupported = []
    for atom in atoms:
        spec = definitions.get(atom)
        if not spec:
            unsupported.append(atom)
            continue
        valid_selectors = spec.get("valid_selectors") or []
        if selector is None:
            unsupported.append(f"{atom}:selector_unresolved")
            continue
        if valid_selectors and selector not in valid_selectors:
            unsupported.append(f"{atom}:selector_not_supported:{selector}")
            continue
        supported.append({
            "atom": atom,
            "metric": spec.get("metric"),
            "definition": spec.get("definition"),
            "safe_article_use": spec.get("safe_article_use"),
            "selector": selector,
        })
    return {
        "supported": supported,
        "unsupported": unsupported,
        "case_engine_ready": bool(supported) and not unsupported,
        "resolved_selector": selector,
        "selector_basis": selector_basis,
    }
