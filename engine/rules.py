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


def _scope(rule: dict) -> str:
    # v0.2 provider rules had no explicit scope and are treated as full rules.
    return rule.get("scope", "full")


def verified_mechanics(lottery: str | None = None, play: str | None = None) -> list[dict]:
    out = []
    for r in load_rules():
        if r.get("status") != "verified" or _scope(r) not in {"mechanics", "full"}:
            continue
        if lottery and r.get("lottery") != lottery:
            continue
        if play and r.get("play") != play:
            continue
        out.append(r)
    return out


def verified_economics(provider_id: str | None = None, lottery: str | None = None, play: str | None = None) -> list[dict]:
    out = []
    for r in load_rules():
        if r.get("status") != "verified" or _scope(r) not in {"economics", "full"}:
            continue
        if provider_id and r.get("provider_id") != provider_id:
            continue
        if lottery and r.get("lottery") != lottery:
            continue
        if play and r.get("play") != play:
            continue
        out.append(r)
    return out


def verified_rules(provider_id: str | None = None, lottery: str | None = None, play: str | None = None) -> list[dict]:
    """Backward-compatible full/economic lookup used by v0.2 callers."""
    return verified_economics(provider_id, lottery, play)


def rule_capability(provider_id: str | None, lottery: str, play: str) -> dict:
    mechanics = verified_mechanics(lottery, play)
    economics = verified_economics(provider_id, lottery, play) if provider_id else []
    return {
        "lottery": lottery,
        "play": play,
        "provider_id": provider_id,
        "mechanics_verified": bool(mechanics),
        "economics_verified": bool(economics),
        "can_explain_play": bool(mechanics),
        "can_generate_rule_compliant_example": bool(mechanics),
        "can_state_stake_payout_rebate": bool(economics),
        "mechanics_rule_refs": [r.get("rule_id") for r in mechanics],
        "economics_rule_refs": [r.get("rule_id") for r in economics],
    }


def require_verified_mechanics(lottery: str, play: str) -> dict:
    rows = verified_mechanics(lottery, play)
    if not rows:
        raise LookupError(f"No verified mechanics for lottery={lottery!r}, play={play!r}")
    return rows[0]


def require_verified_economics(provider_id: str, lottery: str, play: str) -> dict:
    rows = verified_economics(provider_id, lottery, play)
    if not rows:
        raise LookupError(
            f"No verified economics for provider={provider_id!r}, lottery={lottery!r}, play={play!r}"
        )
    return rows[0]


def require_verified_rule(provider_id: str, lottery: str, play: str) -> dict:
    return require_verified_economics(provider_id, lottery, play)
