from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.v2_readiness import readiness_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Report V2 code readiness separately from external runtime dependencies")
    parser.add_argument("--signals", type=Path)
    parser.add_argument("--provider")
    parser.add_argument("--lottery")
    parser.add_argument("--play")
    args = parser.parse_args()
    result = readiness_report(
        signals_path=args.signals,
        provider_id=args.provider,
        lottery=args.lottery,
        play=args.play,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["v2_code_ready"] else 9


if __name__ == "__main__":
    raise SystemExit(main())
