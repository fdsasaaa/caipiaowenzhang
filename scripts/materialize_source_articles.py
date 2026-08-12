from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.source_materialization import materialize_source_file

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Materialize exact collected source article snapshots for provenance/evidence binding."
    )
    parser.add_argument("input", type=Path, help="JSON/JSONL/CSV/Parquet source file containing article bodies")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write immutable source snapshots and manifest; default is dry-run only",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "knowledge" / "source_articles",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "knowledge" / "source_manifests" / "materialized_sources.jsonl",
    )
    args = parser.parse_args()

    result = materialize_source_file(
        args.input,
        root=ROOT,
        output_dir=args.output_dir,
        manifest_path=args.manifest,
        apply=args.apply,
    )
    payload = result.as_dict()
    payload["mode"] = "apply" if args.apply else "dry_run"
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if result.conflicts:
        return 3
    if result.rejected:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
