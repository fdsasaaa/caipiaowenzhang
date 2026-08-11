from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVES = ROOT / "knowledge" / "archives"


def iter_archive_jsonl(path: Path):
    if not path.exists():
        return
    encoded = path.read_text(encoding="ascii").strip()
    if not encoded:
        return
    raw = gzip.decompress(base64.b64decode(encoded))
    for line in raw.decode("utf-8").splitlines():
        if line.strip():
            yield json.loads(line)


def archive_path(name: str) -> Path:
    return ARCHIVES / f"{name}.jsonl.gz.b64"
