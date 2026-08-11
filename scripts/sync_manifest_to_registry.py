from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.store import REGISTRY_FILES, append_jsonl, iter_jsonl


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", type=Path)
    args = ap.parse_args()
    known = {r.get("source_id") for r in iter_jsonl(REGISTRY_FILES["sources"])}
    added = 0
    for line in args.manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("source_id") in known:
            continue
        append_jsonl("sources", row)
        known.add(row.get("source_id"))
        added += 1
    print(json.dumps({"added": added}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
