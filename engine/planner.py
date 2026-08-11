from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .knowledge_io import archive_path, iter_archive_jsonl
from .rules import verified_rules

ROOT = Path(__file__).resolve().parents[1]
CLUSTERS = ROOT / "knowledge" / "technique_clusters" / "brbcw.jsonl"
ARTICLES = ROOT / "registry" / "articles.jsonl"

PLAY_CLASS_ALIASES = {
    "定位胆": "定位胆", "一星": "定位胆", "组选": "组选", "组三": "组选", "组六": "组选",
    "杀号": "杀号", "杀码": "杀号", "胆码": "胆码", "定胆": "胆码", "和值": "和值",
    "跨度": "跨度", "冷热": "冷热", "遗漏": "遗漏", "奇偶大小": "奇偶大小",
    "大小单双": "奇偶大小", "复式": "复式组合", "组合": "复式组合", "倍投": "倍投资金",
    "资金管理": "倍投资金",
}
PLAY_FORBIDDEN_ATOMS = {"定位胆": {"group3_group6"}}


def _rows(path: Path):
    paths = []
    if path.exists():
        paths.append(path)
    paths.extend(sorted(path.parent.glob(path.stem + ".part-*.jsonl")))
    rows = []
    for p in paths:
        rows.extend(json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip())
    if not rows and path == CLUSTERS:
        rows.extend(iter_archive_jsonl(archive_path("brbcw_clusters")))
    return rows


def _matches_play(c: dict, play: str) -> bool:
    target_class = PLAY_CLASS_ALIASES.get(play)
    if not target_class:
        return True
    if target_class not in c.get("source_classifications", []):
        return False
    forbidden = PLAY_FORBIDDEN_ATOMS.get(target_class, set())
    return not bool(forbidden.intersection(c.get("technique_atoms", [])))


def plan_articles(provider_id: str, lottery: str, play: str, count: int = 10) -> dict:
    rules = verified_rules(provider_id, lottery, play)
    clusters = _rows(CLUSTERS)
    existing = _rows(ARTICLES)
    used = {x.get("angle_signature") for x in existing if x.get("angle_signature")}
    seen_new = set()
    ranked = []
    for c in clusters:
        if c.get("article_generation_status") == "idea_only" or not _matches_play(c, play):
            continue
        source_lotteries = c.get("lotteries", [])
        if source_lotteries and lottery not in source_lotteries:
            continue
        angle = f"{provider_id}|{lottery}|{play}|{c.get('family_id')}|{','.join(c.get('positions', []))}"
        angle_hash = hashlib.sha1(angle.encode("utf-8")).hexdigest()[:20]
        if angle_hash in used or angle_hash in seen_new:
            continue
        seen_new.add(angle_hash)
        support, risk = c.get("source_count", 0), c.get("risk_rate", 0)
        ranked.append((support * max(0.05, 1 - risk), support, -risk, angle_hash, c))
    ranked.sort(reverse=True, key=lambda x: (x[0], x[1], x[2]))
    plans = []
    for _, _, _, angle_hash, c in ranked[:count]:
        plans.append({
            "angle_signature": angle_hash, "provider_id": provider_id, "lottery": lottery, "play": play,
            "technique_family": c.get("family_id"), "technique_atoms": c.get("technique_atoms", []),
            "positions": c.get("positions", []), "source_refs": c.get("example_source_ids", []),
            "source_support_count": c.get("source_count", 0), "source_risk_rate": c.get("risk_rate", 0),
            "status": "ready_for_drafting" if rules else "blocked_rule_verification",
            "rule_refs": [r.get("rule_id") for r in rules],
        })
    return {
        "provider_id": provider_id, "lottery": lottery, "play": play, "verified_rule_count": len(rules),
        "status": "ready" if rules else "blocked_rule_verification", "plans": plans,
        "rule_gap": None if rules else {
            "provider_id": provider_id, "lottery": lottery, "play": play,
            "reason": "No verified provider-aware rule is available. Drafting with concrete bet format/cost/payout is blocked."
        }
    }
