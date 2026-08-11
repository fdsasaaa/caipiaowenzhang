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
        "author": row.get("author"),
        "published_at": row.get("published_at"),
        "url": row.get("url"),
        "keywords": row.get("keywords", ""),
        "source_quality_score": row.get("quality_score"),
        "content_length": row.get("content_length", len(content)),
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("--output", type=Path, default=Path("knowledge/source_manifests/brbcw.jsonl"))
    args = ap.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    seen = set()
    with args.output.open("w", encoding="utf-8", newline="\n") as out:
        for row in read_rows(args.input):
            item = normalize(row)
            if item["source_id"] in seen:
                continue
            seen.add(item["source_id"])
            out.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    print(json.dumps({"written": count, "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
