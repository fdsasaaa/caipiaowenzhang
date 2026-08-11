from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_rules() -> list[dict]:
    records: list[dict] = []
    for path in (ROOT / "rules").rglob("*.json"):
        try:
            records.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON rule: {path}: {exc}") from exc
    return records


def verified_rules(lottery: str | None = None, play: str | None = None) -> list[dict]:
    out = []
    for r in load_rules():
        if r.get("status") != "verified":
            continue
        if lottery and r.get("lottery") != lottery:
            continue
        if play and r.get("play") != play:
            continue
        out.append(r)
    return out


def require_verified_rule(lottery: str, play: str) -> dict:
    rows = verified_rules(lottery, play)
    if not rows:
        raise LookupError(f"No verified rule for lottery={lottery!r}, play={play!r}")
    return rows[0]
