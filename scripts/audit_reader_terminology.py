from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.public_terminology import audit_repository


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit reader-facing FFC terminology without touching internal rule/source taxonomy.")
    parser.add_argument("--root", default=".", help="repository root")
    args = parser.parse_args()

    report = audit_repository(Path(args.root).resolve())
    print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    return 0 if report.passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
