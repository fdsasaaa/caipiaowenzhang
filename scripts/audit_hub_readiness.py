#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

from engine.hub_readiness import audit_hub_readiness


def main() -> int:
    report = audit_hub_readiness()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
