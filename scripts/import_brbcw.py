from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

INDEX_SUFFIX = "有价值文章_索引.jsonl"


def source_id(thread_id: object) -> str:
    return f"BRBCW-{int(thread_id):06d}"


def normalize(row: dict) -> dict:
    # Full text is intentionally not copied into the Git manifest.
    content = row.get("cleaned_content", "") or ""
    return {
        "source_id": source_id(row["thread_id"]),
        "source_type": "forum_article",
        "source_name": "brbcw.com",
        "thread_id": row.get("thread_id"),
        "title": row.get("title"),
        "classification": row.get("classification"),
        "published_at": row.get("published_at"),
        "url": row.get("url"),
        "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "claim_status": "unverified",
        "usage": "idea_and_case_source_only"
    }


def read_rows(path: Path):
    if path.is_file() and path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as z:
            matches = [n for n in z.namelist() if n.endswith(INDEX_SUFFIX)]
            if len(matches) != 1:
                raise SystemExit(f"Expected exactly one {INDEX_SUFFIX}, found {len(matches)}")
            for line in z.read(matches[0]).decode("utf-8-sig").splitlines():
                if line.strip():
                    yield json.loads(line)
        return
    index = path / INDEX_SUFFIX if path.is_dir() else path
    for line in index.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            yield json.loads(line)


def write_sharded_jsonl(output: Path, rows: list[dict], max_part_bytes: int = 600_000) -> list[Path]:
    output.parent.mkdir(parents=True, exist_ok=True)
    for old in output.parent.glob(output.stem + ".part-*.jsonl"):
        old.unlink()
    if output.exists():
        output.unlink()
    parts, buffer, size, part_no = [], [], 0, 1
    for row in rows:
        line = json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
        n = len(line.encode("utf-8"))
        if buffer and size + n > max_part_bytes:
            part = output.parent / f"{output.stem}.part-{part_no:03d}.jsonl"
            part.write_text("".join(buffer), encoding="utf-8")
            parts.append(part); part_no += 1; buffer = []; size = 0
        buffer.append(line); size += n
    if buffer:
        part = output.parent / f"{output.stem}.part-{part_no:03d}.jsonl"
        part.write_text("".join(buffer), encoding="utf-8")
        parts.append(part)
    return parts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("--output", type=Path, default=Path("knowledge/source_manifests/brbcw.jsonl"))
    ap.add_argument("--max-part-bytes", type=int, default=600_000)
    args = ap.parse_args()
    seen, normalized = set(), []
    for row in read_rows(args.input):
        item = normalize(row)
        if item["source_id"] in seen:
            continue
        seen.add(item["source_id"]); normalized.append(item)
    parts = write_sharded_jsonl(args.output, normalized, args.max_part_bytes)
    print(json.dumps({"written": len(normalized), "parts": [str(p) for p in parts]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
