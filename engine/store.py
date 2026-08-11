from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .source_sets import iter_brbcw_sources

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry"
VAR = ROOT / "var"
DB = VAR / "index.sqlite3"

REGISTRY_FILES = {
    "articles": REGISTRY / "articles.jsonl",
    "techniques": REGISTRY / "techniques.jsonl",
    "sources": REGISTRY / "sources.jsonl",
}


def ensure_layout() -> None:
    REGISTRY.mkdir(parents=True, exist_ok=True)
    VAR.mkdir(parents=True, exist_ok=True)
    for path in REGISTRY_FILES.values():
        path.touch(exist_ok=True)


def iter_jsonl(path: Path) -> Iterable[dict]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def iter_registry(kind: str):
    """Iterate canonical registry plus optional sharded registry files, deduplicated.

    Shards use registry/<kind>.*.jsonl and exist to keep Git/API file sizes
    manageable as the knowledge base grows. Canonical files may later receive
    incremental records, so IDs are deduplicated across both layers.
    """
    ensure_layout()
    canonical = REGISTRY_FILES[kind]
    key_field = {"articles": "article_id", "techniques": "technique_id", "sources": "source_id"}[kind]
    seen = set()
    paths = [canonical, *sorted(REGISTRY.glob(canonical.stem + ".*.jsonl"))]
    if kind == "sources":
        manifest_dir = ROOT / "knowledge" / "source_manifests"
        paths.extend(sorted(manifest_dir.glob("*.jsonl")))
    for path in paths:
        for row in iter_jsonl(path):
            key = row.get(key_field)
            if key and key in seen:
                continue
            if key:
                seen.add(key)
            yield row
    if kind == "sources":
        for row in iter_brbcw_sources():
            key = row.get(key_field)
            if key and key in seen:
                continue
            if key:
                seen.add(key)
            yield row


def append_jsonl(kind: str, record: dict) -> None:
    ensure_layout()
    path = REGISTRY_FILES[kind]
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def rebuild_index() -> dict:
    ensure_layout()
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.executescript(
        """
        CREATE TABLE articles (
          article_id TEXT PRIMARY KEY,
          title TEXT,
          primary_keyword TEXT,
          search_intent TEXT,
          lottery TEXT,
          play TEXT,
          technique_atoms TEXT,
          case_structure TEXT,
          fingerprint TEXT,
          content_hash TEXT,
          status TEXT,
          published_url TEXT,
          payload TEXT NOT NULL
        );
        CREATE INDEX idx_articles_fp ON articles(fingerprint);
        CREATE INDEX idx_articles_status ON articles(status);
        CREATE TABLE techniques (
          technique_id TEXT PRIMARY KEY,
          name TEXT,
          status TEXT,
          logic TEXT,
          payload TEXT NOT NULL
        );
        CREATE TABLE sources (
          source_id TEXT PRIMARY KEY,
          source_type TEXT,
          title TEXT,
          url TEXT,
          payload TEXT NOT NULL
        );
        """
    )
    counts = {"articles": 0, "techniques": 0, "sources": 0}
    for r in iter_registry("articles"):
        con.execute(
            "INSERT OR REPLACE INTO articles VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                r.get("article_id"), r.get("title"), r.get("primary_keyword"), r.get("search_intent"),
                r.get("lottery"), r.get("play"), json.dumps(r.get("technique_atoms", []), ensure_ascii=False),
                r.get("case_structure"), r.get("fingerprint"), r.get("content_hash"), r.get("status"),
                r.get("published_url"), json.dumps(r, ensure_ascii=False),
            ),
        )
        counts["articles"] += 1
    for r in iter_registry("techniques"):
        con.execute(
            "INSERT OR REPLACE INTO techniques VALUES (?,?,?,?,?)",
            (r.get("technique_id"), r.get("name"), r.get("status"), r.get("logic"), json.dumps(r, ensure_ascii=False)),
        )
        counts["techniques"] += 1
    for r in iter_registry("sources"):
        con.execute(
            "INSERT OR REPLACE INTO sources VALUES (?,?,?,?,?)",
            (r.get("source_id"), r.get("source_type"), r.get("title"), r.get("url"), json.dumps(r, ensure_ascii=False)),
        )
        counts["sources"] += 1
    con.commit()
    con.close()
    return counts


def counts() -> dict:
    ensure_layout()
    return {k: sum(1 for _ in iter_registry(k)) for k in REGISTRY_FILES}
