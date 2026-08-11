from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path


def read_cards(path: Path) -> list[dict]:
    paths = [path] if path.is_file() else sorted(path.glob("*.jsonl"))
    rows: list[dict] = []
    for item in paths:
        for line in item.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _family_key(card: dict) -> str:
    atoms = sorted(set(card.get("technique_atoms") or []))
    return ",".join(atoms)


def _family_id(key: str) -> str:
    return "FAM2-" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def build_dynamic_families(cards: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for card in cards:
        if card.get("knowledge_status") != "eligible_after_rule_binding":
            continue
        if card.get("quality", {}).get("decision") != "keep":
            continue
        if not card.get("technique_atoms"):
            continue
        groups[_family_key(card)].append(card)

    families: list[dict] = []
    for key, rows in groups.items():
        atoms = key.split(",") if key else []
        positions = sorted({x for row in rows for x in (row.get("positions") or [])})
        lotteries = sorted({x for row in rows for x in (row.get("lotteries") or [])})
        classes = set()
        for row in rows:
            classes.update(str(x) for x in (row.get("topic_tags") or []) if x)
            classification = str(row.get("classification") or "").strip()
            if classification:
                classes.add(classification)
        risky = sum(1 for row in rows if int(row.get("claim_risk_max") or 0) >= 85)
        example_ids = [str(row.get("source_id")) for row in rows if row.get("source_id")][:5]
        families.append({
            "family_id": _family_id(key),
            "family_version": "2.0",
            "origin": "dynamic_source_intelligence_v2",
            "source_count": len(rows),
            "risk_rate": risky / len(rows) if rows else 0.0,
            "lotteries": lotteries,
            "positions": positions,
            "technique_atoms": atoms,
            "source_classifications": sorted(classes),
            "example_source_ids": example_ids,
            "article_generation_status": "eligible_after_rule_binding",
        })
    return sorted(families, key=lambda row: (-row["source_count"], row["family_id"]))


def write_dynamic_families(cards_path: Path, output_path: Path) -> dict:
    cards = read_cards(cards_path)
    families = build_dynamic_families(cards)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in families),
        encoding="utf-8",
    )
    return {
        "cards_read": len(cards),
        "families_written": len(families),
        "sources_indexed": sum(row["source_count"] for row in families),
        "output": str(output_path),
    }
