from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


class DrawResearchError(ValueError):
    pass


@dataclass
class DrawDatasetReport:
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    dataset_hash: str | None = None
    record_count: int = 0


_REQUIRED_POSITIONS = ["万", "千", "百", "十", "个"]


def canonical_records(records: list[dict]) -> str:
    return json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def records_sha256(records: list[dict]) -> str:
    return hashlib.sha256(canonical_records(records).encode("utf-8")).hexdigest()


def _digits(record: dict) -> list[int]:
    value = record.get("digits")
    if not isinstance(value, list) or len(value) != 5:
        raise DrawResearchError("each record must contain exactly five digits")
    out: list[int] = []
    for digit in value:
        if isinstance(digit, bool) or not isinstance(digit, int) or digit < 0 or digit > 9:
            raise DrawResearchError("draw digits must be integers from 0 to 9")
        out.append(digit)
    return out


def validate_draw_dataset(dataset: dict) -> DrawDatasetReport:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(dataset, dict):
        return DrawDatasetReport(False, ["dataset must be a JSON object"])

    if dataset.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    if not str(dataset.get("dataset_id") or "").strip():
        errors.append("dataset_id is required")
    if str(dataset.get("lottery") or "").strip() != "时时彩":
        errors.append("V1.2 draw research currently accepts only the verified 时时彩 mechanics family")
    if dataset.get("positions") != _REQUIRED_POSITIONS:
        errors.append("positions must be exactly 万/千/百/十/个 in canonical order")

    provenance = dataset.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("provenance object is required")
        provenance = {}
    if provenance.get("verification_status") != "verified_external":
        errors.append("historical data is research-eligible only after external provenance verification")
    if not str(provenance.get("source_note") or "").strip():
        errors.append("provenance.source_note is required")
    if not str(provenance.get("collected_at") or "").strip():
        errors.append("provenance.collected_at is required")

    records = dataset.get("records")
    if not isinstance(records, list) or not records:
        errors.append("records must be a non-empty list")
        return DrawDatasetReport(False, errors, warnings)

    seen_issues: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"records[{index}] must be an object")
            continue
        issue = str(record.get("issue") or "").strip()
        if not issue:
            errors.append(f"records[{index}] issue is required")
            continue
        if issue in seen_issues:
            errors.append(f"duplicate issue: {issue}")
            continue
        seen_issues.add(issue)
        try:
            digits = _digits(record)
        except DrawResearchError as exc:
            errors.append(f"records[{index}]: {exc}")
            continue
        normalized.append({"issue": issue, "digits": digits})

    digest = records_sha256(normalized) if normalized else None
    declared_hash = str(provenance.get("records_sha256") or "").strip().lower()
    if not declared_hash:
        errors.append("provenance.records_sha256 is required")
    elif digest and declared_hash != digest:
        errors.append("provenance.records_sha256 does not match normalized records")

    if len(normalized) < 50:
        warnings.append("dataset has fewer than 50 records; use only for exploratory idea generation")

    return DrawDatasetReport(
        passed=not errors,
        errors=errors,
        warnings=warnings,
        dataset_hash=digest,
        record_count=len(normalized),
    )


def _position_frequencies(records: list[dict]) -> dict[str, list[int]]:
    counts = {position: [0] * 10 for position in _REQUIRED_POSITIONS}
    for record in records:
        digits = _digits(record)
        for index, position in enumerate(_REQUIRED_POSITIONS):
            counts[position][digits[index]] += 1
    return counts


def _relationship_summary(records: list[dict]) -> dict:
    last2_abs_diff = [0] * 10
    last3_span = [0] * 10
    last2_sum_mod5 = [0] * 5
    for record in records:
        digits = _digits(record)
        tens, units = digits[3], digits[4]
        last2_abs_diff[abs(tens - units)] += 1
        last2_sum_mod5[(tens + units) % 5] += 1
        tail3 = digits[2:]
        last3_span[max(tail3) - min(tail3)] += 1
    return {
        "后二绝对差分布": last2_abs_diff,
        "后二和值mod5分布": last2_sum_mod5,
        "后三跨度分布": last3_span,
    }


def build_draw_research_context(dataset: dict, *, recent_limit: int = 80, sample_limit: int = 80) -> dict:
    report = validate_draw_dataset(dataset)
    if not report.passed:
        raise DrawResearchError("; ".join(report.errors))

    records = [{"issue": str(row["issue"]), "digits": _digits(row)} for row in dataset["records"]]
    total = len(records)
    recent = records[-min(recent_limit, total):]

    if total <= sample_limit:
        sample = records
    else:
        indexes = sorted({round(i * (total - 1) / (sample_limit - 1)) for i in range(sample_limit)})
        sample = [records[i] for i in indexes]

    return {
        "dataset_id": dataset["dataset_id"],
        "dataset_hash": report.dataset_hash,
        "record_count": total,
        "positions": list(_REQUIRED_POSITIONS),
        "first_issue": records[0]["issue"],
        "last_issue": records[-1]["issue"],
        "position_digit_frequencies": _position_frequencies(records),
        "relationship_summary": _relationship_summary(records),
        "recent_records": recent,
        "stratified_sample": sample,
        "research_role": "private hypothesis/idea input only; not publication evidence in V1.2",
        "guardrails": [
            "历史分布只用于提出新技巧假设，不等于未来预测优势",
            "V1.2最终文章不得引用这些历史统计数字作为公开事实，因为正式 historical-evidence 通道尚未启用",
            "可以把从数据得到的灵感转化为新的可复算结构，再用 synthetic_case 演示",
            "不要根据同一批历史数据反复调参数直到得到漂亮结果",
            "不要把样本内表现写成命中率、盈利能力或未来保证",
        ],
    }
