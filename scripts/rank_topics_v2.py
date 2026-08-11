from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.seo_priority import rank_generated_topics, read_demand_signals


def main() -> int:
    parser = argparse.ArgumentParser(description="Rank candidate article topics before model generation")
    parser.add_argument("--provider", required=True)
    parser.add_argument("--lottery", required=True)
    parser.add_argument("--play", required=True)
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--signals", type=Path, help="optional normalized Search Console/search-demand JSON or JSONL")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    signals = read_demand_signals(args.signals)
    result = rank_generated_topics(args.provider, args.lottery, args.play, args.count, signals)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["eligible"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
