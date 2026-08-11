from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .rules import rule_capability
from .knowledge_io import iter_brbcw_families
from .technique_semantics import case_requirements, selector_variants

ROOT = Path(__file__).resolve().parents[1]
CLUSTERS = ROOT / "knowledge" / "technique_clusters" / "brbcw.jsonl"
DYNAMIC_FAMILIES = ROOT / "knowledge" / "dynamic_families"
ARTICLES = ROOT / "registry" / "articles.jsonl"

PLAY_CLASS_ALIASES = {
    "定位胆": "定位胆", "一星": "定位胆", "组选": "组选", "组三": "组选", "组六": "组选",
    "后二组选": "组选", "前二组选": "组选", "后三组选3": "组选", "后三组选6": "组选",
    "前三组选3": "组选", "前三组选6": "组选", "中三组选3": "组选", "中三组选6": "组选",
    "杀号": "杀号", "杀码": "杀号", "胆码": "胆码", "定胆": "胆码", "和值": "和值",
    "跨度": "跨度", "冷热": "冷热", "遗漏": "遗漏", "奇偶大小": "奇偶大小",
    "大小单双": "奇偶大小", "后二大小单双": "奇偶大小", "复式": "复式组合", "组合": "复式组合",
    "倍投": "倍投资金", "资金管理": "倍投资金",
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
        for f in iter_brbcw_families():
            rows.append({
                "family_id": f.get("f"), "source_count": f.get("n", 0), "risk_rate": f.get("r", 0),
                "lotteries": f.get("l", []), "positions": f.get("p", []), "technique_atoms": f.get("a", []),
                "source_classifications": f.get("c", []), "example_source_ids": f.get("e", []),
                "article_generation_status": "eligible_after_rule_binding" if f.get("a") else "idea_only",
            })
    return rows


def _dynamic_rows() -> list[dict]:
    if not DYNAMIC_FAMILIES.exists():
        return []
    rows: list[dict] = []
    for path in sorted(DYNAMIC_FAMILIES.glob("*.jsonl")):
        rows.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    return rows


def _all_clusters() -> list[dict]:
    static = _rows(CLUSTERS)
    dynamic = _dynamic_rows()
    seen: set[str] = set()
    out: list[dict] = []
    for row in [*static, *dynamic]:
        family_id = str(row.get("family_id") or "")
        if family_id and family_id in seen:
            continue
        if family_id:
            seen.add(family_id)
        out.append(row)
    return out


def _matches_play(c: dict, play: str) -> bool:
    target_class = PLAY_CLASS_ALIASES.get(play)
    if not target_class:
        return True
    if target_class not in c.get("source_classifications", []):
        return False
    forbidden = PLAY_FORBIDDEN_ATOMS.get(target_class, set())
    return not bool(forbidden.intersection(c.get("technique_atoms", [])))


def _plan_status(cap: dict) -> str:
    if not cap["mechanics_verified"]:
        return "blocked_mechanics_verification"
    if cap["economics_verified"]:
        return "ready_full"
    return "ready_mechanics_only"


def _angle_hash(provider_id: str, lottery: str, play: str, family: str, selector: str | None) -> str:
    raw = f"{provider_id}|{lottery}|{play}|{family}|selector={selector or ''}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]


def plan_articles(provider_id: str, lottery: str, play: str, count: int = 10) -> dict:
    cap = rule_capability(provider_id, lottery, play)
    clusters = _all_clusters()
    existing = _rows(ARTICLES)
    used = {x.get("angle_signature") for x in existing if x.get("angle_signature")}
    ranked = []
    for c in clusters:
        if c.get("article_generation_status") == "idea_only" or not _matches_play(c, play):
            continue
        source_lotteries = c.get("lotteries", [])
        if source_lotteries and lottery not in source_lotteries:
            continue
        support, risk = c.get("source_count", 0), c.get("risk_rate", 0)
        ranked.append((support * max(0.05, 1 - risk), support, -risk, c))
    ranked.sort(reverse=True, key=lambda x: (x[0], x[1], x[2]))

    status = _plan_status(cap)
    rule_refs = cap["mechanics_rule_refs"] + cap["economics_rule_refs"]
    plans = []
    seen_new = set()
    for _, _, _, c in ranked:
        atoms = c.get("technique_atoms", [])
        positions = c.get("positions", [])
        variants = selector_variants(play, positions, atoms)
        if not variants:
            continue
        for selector_info in variants:
            selector = selector_info.get("selector")
            angle_hash = _angle_hash(
                provider_id, lottery, play, str(c.get("family_id") or ""), str(selector or "")
            )
            if angle_hash in used or angle_hash in seen_new:
                continue
            seen_new.add(angle_hash)
            case_plan = case_requirements(atoms, selector, selector_info.get("basis"))
            case_plan["source_position_supported"] = bool(selector_info.get("source_position_supported"))
            plans.append({
                "angle_signature": angle_hash,
                "provider_id": provider_id,
                "lottery": lottery,
                "play": play,
                "technique_family": c.get("family_id"),
                "technique_atoms": atoms,
                "positions": positions,
                "resolved_selector": selector,
                "selector_basis": selector_info.get("basis"),
                "source_refs": c.get("example_source_ids", []),
                "source_support_count": c.get("source_count", 0),
                "source_risk_rate": c.get("risk_rate", 0),
                "knowledge_origin": c.get("origin") or "legacy_static",
                "status": status,
                "rule_refs": rule_refs,
                "allowed_case_scope": "economics" if cap["economics_verified"] else ("mechanics_only" if cap["mechanics_verified"] else "idea_only"),
                "case_plan": case_plan,
            })
            if len(plans) >= count:
                break
        if len(plans) >= count:
            break

    gaps = []
    if not cap["mechanics_verified"]:
        gaps.append({"gap_type": "mechanics", "lottery": lottery, "play": play})
    if provider_id and not cap["economics_verified"]:
        gaps.append({"gap_type": "economics", "provider_id": provider_id, "lottery": lottery, "play": play})
    return {
        "provider_id": provider_id,
        "lottery": lottery,
        "play": play,
        "status": status,
        "capability": cap,
        "plans": plans,
        "rule_gaps": gaps,
        "knowledge_sources": {
            "static_families": len(_rows(CLUSTERS)),
            "dynamic_families": len(_dynamic_rows()),
        },
    }
