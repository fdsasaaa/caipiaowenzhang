from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source_intelligence import ingest_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert normalized source JSON/JSONL into v2 knowledge cards")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--quarantine", type=Path)
    args = parser.parse_args()
    result = ingest_file(args.input, args.output, args.quarantine)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
