#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.public_release_revision import (
    stage_public_release_revision,
    write_public_release_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage an approved website public-release revision without mutating its parent package.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--expected-count", type=int, required=True)
    parser.add_argument("--approved-root", type=Path)
    parser.add_argument("--release-root", type=Path)
    parser.add_argument("--manifest-root", type=Path)
    args = parser.parse_args()

    package = json.loads(args.input.read_text(encoding="utf-8"))
    staged = stage_public_release_revision(
        package,
        approved_root=args.approved_root,
        release_root=args.release_root,
    )
    manifest = write_public_release_manifest(
        staged["source_batch_id"],
        expected_count=args.expected_count,
        approved_root=args.approved_root,
        release_root=args.release_root,
        manifest_root=args.manifest_root,
    )
    print(json.dumps({"staged": staged, "manifest": manifest}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
