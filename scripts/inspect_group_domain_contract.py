from __future__ import annotations

import json

from engine.group_domain_contract import high_leverage_family_domain_diagnostic


def main() -> int:
    print(json.dumps(high_leverage_family_domain_diagnostic(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
