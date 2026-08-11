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


def iter_sharded_b64_gzip_jsonl(pattern: str):
    parts = sorted((ROOT / "knowledge").glob(pattern))
    if not parts:
        return
    encoded = "".join(p.read_text(encoding="ascii").strip() for p in parts)
    raw = gzip.decompress(base64.b64decode(encoded))
    for line in raw.decode("utf-8").splitlines():
        if line.strip():
            yield json.loads(line)


def iter_brbcw_families():
    yield from iter_sharded_b64_gzip_jsonl("family_archives/brbcw_families_compact.part-*.b64")
