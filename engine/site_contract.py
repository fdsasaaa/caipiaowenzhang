from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "publishing" / "LAOCAIMI_SITE_CONTRACT.json"


@lru_cache(maxsize=1)
def load_site_contract() -> dict:
    data = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("content_types"), dict):
        raise ValueError("invalid laocaimi site contract")
    return data


def site_category_for(content_type: str) -> str:
    row = load_site_contract()["content_types"].get(content_type)
    if not isinstance(row, dict) or not row.get("site_category_key"):
        raise LookupError(f"unknown content_type for laocaimi: {content_type!r}")
    return str(row["site_category_key"])


def required_content_format() -> str:
    value = str(load_site_contract().get("required_content_format", "")).strip().lower()
    if not value:
        raise ValueError("required_content_format missing from site contract")
    return value


def default_content_type() -> str:
    value = str(load_site_contract().get("current_generator_default", {}).get("content_type", "")).strip()
    if not value:
        raise ValueError("current generator default content_type missing")
    return value
