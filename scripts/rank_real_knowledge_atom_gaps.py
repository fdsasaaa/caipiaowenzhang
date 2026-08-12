from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.real_knowledge_atom_gaps import build_atom_gap_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Rank unbound real-knowledge technique atoms without enabling them.")
    parser.add_argument("--output", help="optional JSON output path")
    args = parser.parse_args()

    report = build_atom_gap_report()
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    print(text)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
