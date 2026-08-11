from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.import_brbcw import read_rows, source_id
TAXONOMY_PATH = ROOT / "knowledge" / "TECHNIQUE_TAXONOMY.json"


def load_taxonomy() -> dict:
    return json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))


def _contains_pattern(text: str, patterns: list[str]) -> bool:
    for p in patterns:
        if re.search(p, text, re.I):
            return True
    return False


def infer_terms(text: str, mapping: dict[str, list[str]]) -> list[str]:
    found = []
    low = text.lower()
    for name, terms in mapping.items():
        if any(t.lower() in low for t in terms):
            found.append(name)
    return found


def extract_percentages(text: str) -> list[dict]:
    out = []
    for m in re.finditer(r"(?<!\d)(\d{1,3}(?:\.\d+)?)\s*%", text):
        value = float(m.group(1))
        if value > 100:
            continue
        out.append({"value": value, "status": "unverified_claim"})
    return out[:8]


def extract_case_numbers(text: str) -> list[str]:
    vals = []
    for pat in [r"(?<!\d)\d{3,5}(?!\d)", r"(?<!\d)[0-9](?:[,、 ]+[0-9]){2,8}(?!\d)"]:
        for m in re.finditer(pat, text):
            v = re.sub(r"\s+", " ", m.group(0)).strip()
            if v not in vals:
                vals.append(v)
            if len(vals) >= 8:
                return vals
    return vals


def extract_case_features(text: str) -> dict:
    history_windows = []
    for pat in [r"近\s*(\d{1,5})\s*期", r"统计\s*(\d{1,5})\s*期", r"前\s*(\d{1,5})\s*期"]:
        for m in re.finditer(pat, text):
            n = int(m.group(1))
            if 1 <= n <= 100000 and n not in history_windows:
                history_windows.append(n)
    omission_triggers = []
    for m in re.finditer(r"遗漏\s*(\d{1,4})\s*期", text):
        n = int(m.group(1))
        if 1 <= n <= 10000 and n not in omission_triggers:
            omission_triggers.append(n)
    return {
        "has_explicit_example": bool(re.search(r"例如|比如|举例|以.{0,20}为例", text)),
        "uses_previous_draw": bool(re.search(r"上期|上一期|当期开奖号|上期开奖", text)),
        "targets_next_draw": bool(re.search(r"下期|下一期|本期", text)),
        "has_tabular_staking_plan": bool(re.search(r"期数.{0,30}(投入|倍数|累计)|累计投入|收益率", text, re.S)),
        "history_windows": history_windows[:8],
        "omission_trigger_periods": omission_triggers[:8],
    }


def make_candidate(row: dict, taxonomy: dict) -> dict:
    text = f"{row.get('title','')}\n{row.get('keywords','')}\n{row.get('cleaned_content','')}"
    atoms = [name for name, patterns in taxonomy["canonical_atoms"].items() if _contains_pattern(text, patterns)]
    lotteries = infer_terms(text, taxonomy["lottery_terms"])
    positions = [p for p in taxonomy["positions"] if p in text]
    topic_tags = []
    for category, terms in taxonomy["categories"].items():
        if any(t in text for t in terms):
            topic_tags.append(category)
    risk_flags = [t for t in taxonomy["claim_risk_terms"] if t.lower() in text.lower()]
    if any(t in text for t in taxonomy["money_claim_terms"]):
        risk_flags.append("money_or_profit_claim")
    claimed = extract_percentages(text)
    if claimed:
        risk_flags.append("percentage_claim")
    sid = source_id(row["thread_id"])
    signature_basis = "|".join(sorted(set(atoms)) + sorted(set(positions)) + [row.get("classification", "")])
    signature = hashlib.sha1(signature_basis.encode("utf-8")).hexdigest()[:16]
    return {
        "candidate_id": f"TC-{sid}",
        "source_id": sid,
        "source_classification": row.get("classification", ""),
        "lotteries": sorted(set(lotteries)),
        "positions": sorted(set(positions)),
        "technique_atoms": sorted(set(atoms)),
        "topic_tags": sorted(set(topic_tags)),
        "claimed_percentages": claimed,
        "risk_flags": sorted(set(risk_flags)),
        "case_numbers": extract_case_numbers(row.get("cleaned_content", "")),
        "case_features": extract_case_features(row.get("cleaned_content", "")),
        "verification_status": "unverified_source",
        "publishable": False,
        "requires_rule_binding": True,
        "signature": signature,
    }


def build_clusters(candidates: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for c in candidates:
        signature_text = "|".join([
            c.get("source_classification", ""),
            ",".join(c.get("technique_atoms", [])),
            ",".join(c.get("positions", [])),
        ])
        key = hashlib.sha1(signature_text.encode("utf-8")).hexdigest()[:16]
        groups[key].append(c)

    clusters = []
    for key, items in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        atoms = sorted({a for x in items for a in x.get("technique_atoms", [])})
        lotteries = sorted({a for x in items for a in x.get("lotteries", [])})
        positions = sorted({a for x in items for a in x.get("positions", [])})
        classes = sorted({x.get("source_classification", "") for x in items if x.get("source_classification")})
        risky = sum(1 for x in items if x.get("risk_flags"))
        signature = f"{' + '.join(atoms) or 'unspecified'} @ {'/'.join(positions) or 'any-position'}"
        family_text = ",".join(atoms) or "unspecified"
        family_id = "FAM-" + hashlib.sha1(family_text.encode("utf-8")).hexdigest()[:16]
        clusters.append({
            "cluster_id": f"CL-{key}",
            "family_id": family_id,
            "signature": signature,
            "source_count": len(items),
            "source_classifications": classes,
            "lotteries": lotteries,
            "positions": positions,
            "technique_atoms": atoms,
            "example_source_ids": [x["source_id"] for x in items[:10]],
            "risk_rate": round(risky / len(items), 4),
            "verification_status": "unverified_source",
            "article_generation_status": "eligible_after_rule_binding" if atoms else "idea_only",
        })
    return clusters


def coverage(candidates: list[dict], clusters: list[dict]) -> dict:
    return {
        "version": "0.2.0",
        "sources": len(candidates),
        "clusters": len(clusters),
        "sources_with_atoms": sum(bool(x["technique_atoms"]) for x in candidates),
        "sources_without_atoms": sum(not x["technique_atoms"] for x in candidates),
        "sources_with_risk_flags": sum(bool(x["risk_flags"]) for x in candidates),
        "classifications": dict(Counter(x["source_classification"] for x in candidates)),
        "lotteries": dict(Counter(a for x in candidates for a in x["lotteries"])),
        "positions": dict(Counter(a for x in candidates for a in x["positions"])),
        "technique_atoms": dict(Counter(a for x in candidates for a in x["technique_atoms"])),
        "topic_tags": dict(Counter(a for x in candidates for a in x["topic_tags"])),
        "note": "All extracted source techniques are unverified ideas. Rule binding and validation are required before article generation."
    }


def write_jsonl(path: Path, rows: list[dict], max_part_bytes: int = 600_000) -> list[Path]:
    path.parent.mkdir(parents=True, exist_ok=True)
    for old in path.parent.glob(path.stem + ".part-*.jsonl"):
        old.unlink()
    if path.exists():
        path.unlink()
    parts, buffer, size, part_no = [], [], 0, 1
    for row in rows:
        line = json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
        n = len(line.encode("utf-8"))
        if buffer and size + n > max_part_bytes:
            part = path.parent / f"{path.stem}.part-{part_no:03d}.jsonl"
            part.write_text("".join(buffer), encoding="utf-8")
            parts.append(part); part_no += 1; buffer = []; size = 0
        buffer.append(line); size += n
    if buffer:
        part = path.parent / f"{path.stem}.part-{part_no:03d}.jsonl"
        part.write_text("".join(buffer), encoding="utf-8")
        parts.append(part)
    return parts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("--candidates", type=Path, default=ROOT / "knowledge" / "technique_candidates" / "brbcw.jsonl")
    ap.add_argument("--clusters", type=Path, default=ROOT / "knowledge" / "technique_clusters" / "brbcw.jsonl")
    ap.add_argument("--coverage", type=Path, default=ROOT / "knowledge" / "coverage" / "brbcw.json")
    ap.add_argument("--max-part-bytes", type=int, default=600_000)
    args = ap.parse_args()
    tax = load_taxonomy()
    candidates = [make_candidate(row, tax) for row in read_rows(args.input)]
    clusters = build_clusters(candidates)
    candidate_parts = write_jsonl(args.candidates, candidates, args.max_part_bytes)
    cluster_parts = write_jsonl(args.clusters, clusters, args.max_part_bytes)
    args.coverage.parent.mkdir(parents=True, exist_ok=True)
    args.coverage.write_text(json.dumps(coverage(candidates, clusters), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"candidates": len(candidates), "clusters": len(clusters), "candidate_parts": [str(p) for p in candidate_parts], "cluster_parts": [str(p) for p in cluster_parts], "coverage": str(args.coverage)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
