#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.formal_approved_inventory import FormalInventoryError, stage_formal_approved_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage one already-approved package into articles/approved without scheduling or publishing")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--approved-root", type=Path, help="override inventory root for tests/controlled workflows")
    args = parser.parse_args()

    try:
        result = stage_formal_approved_file(args.input, approved_root=args.approved_root)
    except FormalInventoryError as exc:
        print(json.dumps({"status": "rejected", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 6

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
