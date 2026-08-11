from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_rules() -> list[dict]:
    records: list[dict] = []
    for path in (ROOT / "rules").rglob("*.json"):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(record, dict) and "rule_id" in record:
                records.append(record)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON rule: {path}: {exc}") from exc
    return records


def verified_rules(provider_id: str | None = None, lottery: str | None = None, play: str | None = None) -> list[dict]:
    out = []
    for r in load_rules():
        if r.get("status") != "verified":
            continue
        if provider_id and r.get("provider_id") != provider_id:
            continue
        if lottery and r.get("lottery") != lottery:
            continue
        if play and r.get("play") != play:
            continue
        out.append(r)
    return out


def require_verified_rule(provider_id: str, lottery: str, play: str) -> dict:
    rows = verified_rules(provider_id, lottery, play)
    if not rows:
        raise LookupError(
            f"No verified rule for provider={provider_id!r}, lottery={lottery!r}, play={play!r}"
        )
    return rows[0]
