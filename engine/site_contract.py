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


def allowed_seo_cluster_ids() -> tuple[str, ...]:
    row = load_site_contract().get("seo_cluster_contract", {})
    values = row.get("allowed_cluster_ids", []) if isinstance(row, dict) else []
    if not isinstance(values, list) or not values:
        raise ValueError("seo cluster allowed ids missing from site contract")
    normalized = tuple(str(value).strip() for value in values if str(value).strip())
    if len(normalized) != len(values) or len(set(normalized)) != len(normalized):
        raise ValueError("invalid or duplicate seo cluster ids in site contract")
    return normalized


def normalize_seo_cluster_assignment(primary: object = None, secondary: object = None) -> tuple[str | None, list[str]]:
    primary_id = str(primary or "").strip() or None
    secondary_ids = [] if secondary in (None, "") else secondary
    if not isinstance(secondary_ids, list):
        raise ValueError("secondary_seo_cluster_ids must be a list")
    normalized_secondary = [str(value).strip() for value in secondary_ids]
    if any(not value for value in normalized_secondary):
        raise ValueError("secondary_seo_cluster_ids contains an empty id")
    if not primary_id and normalized_secondary:
        raise ValueError("secondary SEO clusters require a primary SEO cluster")
    if len(set(normalized_secondary)) != len(normalized_secondary):
        raise ValueError("duplicate secondary SEO cluster id")
    allowed = set(allowed_seo_cluster_ids())
    if primary_id and primary_id not in allowed:
        raise ValueError(f"unknown primary SEO cluster id: {primary_id}")
    for cluster_id in normalized_secondary:
        if cluster_id not in allowed:
            raise ValueError(f"unknown secondary SEO cluster id: {cluster_id}")
    if primary_id and primary_id in normalized_secondary:
        raise ValueError("primary SEO cluster must not repeat in secondary clusters")
    return primary_id, normalized_secondary
