from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .source_intelligence import read_source_rows

GROUP3_TERMS = ("组三", "组选3", "组选三")
GROUP6_TERMS = ("组六", "组选6", "组选六")
DAN_TERMS = ("胆码", "定胆", "定码")


class SourceMaterializationError(ValueError):
    pass


@dataclass
class MaterializationResult:
    input_rows: int = 0
    materialized: int = 0
    unchanged: int = 0
    rejected: int = 0
    conflicts: int = 0
    records: list[dict] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.conflicts == 0

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "input_rows": self.input_rows,
            "materialized": self.materialized,
            "unchanged": self.unchanged,
            "rejected": self.rejected,
            "conflicts": self.conflicts,
            "records": self.records,
        }


def _content(row: dict) -> str:
    for key in ("cleaned_content", "content_text", "content", "body", "text"):
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return ""


def canonical_source_id(row: dict) -> str:
    existing = str(row.get("source_id") or "").strip()
    if existing:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{2,127}", existing):
            raise SourceMaterializationError("source_id contains unsupported characters")
        return existing

    source_name = str(row.get("source_name") or row.get("source") or "").strip().upper()
    native = str(row.get("thread_id") or row.get("id") or "").strip()
    if source_name == "BRBCW" and native.isdigit():
        return f"BRBCW-{int(native):06d}"
    raise SourceMaterializationError("materialization requires an explicit source_id or BRBCW numeric thread_id")


def _literal_occurrences(text: str, terms: tuple[str, ...]) -> list[dict]:
    rows: list[dict] = []
    for term in terms:
        start = 0
        while True:
            index = text.find(term, start)
            if index < 0:
                break
            rows.append({"term": term, "char_start": index, "char_end": index + len(term)})
            start = index + len(term)
    rows.sort(key=lambda row: (row["char_start"], row["term"]))
    return rows


def exact_term_index(title: str, content: str) -> dict:
    combined = f"{title}\n{content}" if title else content
    return {
        "group3_terms": _literal_occurrences(combined, GROUP3_TERMS),
        "group6_terms": _literal_occurrences(combined, GROUP6_TERMS),
        "dan_terms": _literal_occurrences(combined, DAN_TERMS),
        "legacy_ssc_term_count": combined.count("时时彩"),
        "ffc_term_count": combined.count("分分彩"),
    }


def build_materialized_source_record(row: dict) -> dict:
    source_id = canonical_source_id(row)
    content = _content(row)
    if not content.strip():
        raise SourceMaterializationError(f"source {source_id} has no materializable article body")
    title = str(row.get("title") or "").strip()
    content_sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return {
        "schema_version": "1.0",
        "source_id": source_id,
        "source_name": row.get("source_name") or row.get("source") or "unknown",
        "native_id": row.get("thread_id") or row.get("id"),
        "url": row.get("url"),
        "title": title,
        "classification": row.get("classification") or row.get("forum_name") or "",
        "published_at": row.get("published_at"),
        "content": content,
        "content_sha256": content_sha,
        "content_length": len(content),
        "exact_term_index": exact_term_index(title, content),
        "raw_source_policy": {
            "preserve_exact_source_text": True,
            "reader_facing_rewrite_happens_downstream": True,
            "reader_display_preference": "分分彩",
            "legacy_ssc_term_may_remain_in_raw_source": True,
            "raw_source_text_mutated": False,
        },
        "verification_status": "materialized_source_snapshot_unverified_claims",
        "publishable": False,
    }


def _record_path(output_dir: Path, source_id: str) -> Path:
    return output_dir / f"{source_id}.json"


def _manifest_row(record: dict, path: Path, root: Path) -> dict:
    return {
        "source_id": record["source_id"],
        "path": str(path.relative_to(root)).replace("\\", "/"),
        "title": record["title"],
        "url": record.get("url"),
        "classification": record.get("classification"),
        "content_sha256": record["content_sha256"],
        "content_length": record["content_length"],
        "group3_term_count": len(record["exact_term_index"]["group3_terms"]),
        "group6_term_count": len(record["exact_term_index"]["group6_terms"]),
        "dan_term_count": len(record["exact_term_index"]["dan_terms"]),
        "legacy_ssc_term_count": record["exact_term_index"]["legacy_ssc_term_count"],
        "ffc_term_count": record["exact_term_index"]["ffc_term_count"],
        "raw_source_text_mutated": False,
    }


def materialize_source_file(
    input_path: Path,
    *,
    root: Path,
    output_dir: Path | None = None,
    manifest_path: Path | None = None,
    apply: bool = False,
) -> MaterializationResult:
    root = root.resolve()
    output_dir = (output_dir or (root / "knowledge" / "source_articles")).resolve()
    manifest_path = (manifest_path or (root / "knowledge" / "source_manifests" / "materialized_sources.jsonl")).resolve()
    result = MaterializationResult()
    planned: list[tuple[dict, Path]] = []

    for row in read_source_rows(input_path):
        result.input_rows += 1
        try:
            record = build_materialized_source_record(row)
        except SourceMaterializationError as exc:
            result.rejected += 1
            result.records.append({"status": "rejected", "error": str(exc)})
            continue

        path = _record_path(output_dir, record["source_id"])
        if path.exists():
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                result.conflicts += 1
                result.records.append({"source_id": record["source_id"], "status": "conflict", "error": str(exc)})
                continue
            if existing.get("content_sha256") != record["content_sha256"]:
                result.conflicts += 1
                result.records.append({
                    "source_id": record["source_id"],
                    "status": "conflict",
                    "error": "existing materialized source has different content_sha256; snapshots are immutable",
                    "existing_sha256": existing.get("content_sha256"),
                    "incoming_sha256": record["content_sha256"],
                })
                continue
            result.unchanged += 1
            result.records.append({"source_id": record["source_id"], "status": "unchanged", "content_sha256": record["content_sha256"]})
            continue

        planned.append((record, path))
        result.materialized += 1
        result.records.append({
            "source_id": record["source_id"],
            "status": "planned" if not apply else "materialized",
            "content_sha256": record["content_sha256"],
            "path": str(path.relative_to(root)).replace("\\", "/"),
        })

    if apply and result.conflicts == 0:
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_rows: list[dict] = []
        if manifest_path.exists():
            for line in manifest_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    manifest_rows.append(json.loads(line))
        by_source = {str(row["source_id"]): row for row in manifest_rows if row.get("source_id")}
        for record, path in planned:
            path.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            by_source[record["source_id"]] = _manifest_row(record, path, root)
        manifest_path.write_text(
            "".join(json.dumps(by_source[key], ensure_ascii=False, sort_keys=True) + "\n" for key in sorted(by_source)),
            encoding="utf-8",
        )

    return result
