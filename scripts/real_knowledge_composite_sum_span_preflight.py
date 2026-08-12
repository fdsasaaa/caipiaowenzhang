from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.real_knowledge_composition import build_sum_span_composite_evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline real-knowledge cross-family sum/span composition preflight")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    evidence = build_sum_span_composite_evidence()
    text = json.dumps(evidence, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
