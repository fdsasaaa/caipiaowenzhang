from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ALIASES = {
    "query": {"query", "top queries", "queries", "查询", "热门查询", "搜索查询"},
    "clicks": {"clicks", "点击", "点击次数"},
    "impressions": {"impressions", "展示", "展示次数"},
    "ctr": {"ctr", "点击率"},
    "position": {"position", "average position", "排名", "平均排名"},
}


def _norm(value: str) -> str:
    return " ".join((value or "").strip().casefold().split())


def _field_map(fieldnames: list[str]) -> dict[str, str]:
    result = {}
    normalized = {_norm(x): x for x in fieldnames if x}
    for target, aliases in ALIASES.items():
        for alias in aliases:
            if _norm(alias) in normalized:
                result[target] = normalized[_norm(alias)]
                break
    if "query" not in result:
        raise ValueError("Search Console CSV missing query column")
    return result


def _number(value, percent=False):
    text = str(value or "").strip().replace(",", "")
    if not text:
        return None
    if text.endswith("%"):
        return float(text[:-1]) / 100.0
    number = float(text)
    return number / 100.0 if percent and number > 1 else number


def normalize_csv(input_path: Path, output_path: Path) -> dict:
    with input_path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        mapping = _field_map(reader.fieldnames or [])
        rows = []
        for row in reader:
            query = str(row.get(mapping["query"], "") or "").strip()
            if not query:
                continue
            signal = {"query": query, "source": "google_search_console"}
            for field in ("clicks", "impressions", "position"):
                source_col = mapping.get(field)
                if source_col:
                    value = _number(row.get(source_col))
                    if value is not None:
                        signal[field] = value
            if mapping.get("ctr"):
                value = _number(row.get(mapping["ctr"]), percent=True)
                if value is not None:
                    signal["ctr"] = value
            rows.append(signal)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    return {"input": str(input_path), "output": str(output_path), "signals": len(rows)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize a Google Search Console query CSV export")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = normalize_csv(args.input, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
