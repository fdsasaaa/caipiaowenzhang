from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAPS = ROOT / "registry" / "rule_gaps.jsonl"


def gap_id(gap_type: str, lottery: str, play: str, provider_id: str | None = None) -> str:
    raw = f"{gap_type}|{provider_id or '*'}|{lottery}|{play}"
    return "RG-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def list_gaps() -> list[dict]:
    if not GAPS.exists():
        return []
    return [json.loads(line) for line in GAPS.read_text(encoding="utf-8").splitlines() if line.strip()]


def record_gap(gap_type: str, lottery: str, play: str, provider_id: str | None = None, reason: str = "") -> dict:
    GAPS.parent.mkdir(parents=True, exist_ok=True)
    gid = gap_id(gap_type, lottery, play, provider_id)
    existing = {row.get("gap_id"): row for row in list_gaps()}
    if gid in existing:
        return existing[gid]
    row = {
        "gap_id": gid,
        "gap_type": gap_type,
        "provider_id": provider_id,
        "lottery": lottery,
        "play": play,
        "status": "open",
        "reason": reason,
    }
    with GAPS.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return row
