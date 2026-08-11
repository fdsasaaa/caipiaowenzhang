from __future__ import annotations

import hashlib

from .dedup import duplicate_candidates
from .planner import plan_articles
from .semantic_dedup import structural_duplicate_candidates
from .seo_keywords import keyword_owners, primary_keyword_for
from .site_contract import default_content_type, site_category_for
from .text import fingerprint

ATOM_LABELS = {
    "position_filter": "位置筛选",
    "sum_range": "和值区间",
    "span_range": "跨度筛选",
    "odd_even_filter": "奇偶筛选",
    "big_small_filter": "大小筛选",
    "cold_hot_split": "冷热频率",
    "omission_threshold": "遗漏阈值",
    "repeat_number": "重号结构",
    "neighbor_number": "邻号结构",
    "consecutive_number": "连号结构",
    "dan_candidate": "胆码筛选",
    "kill_candidate": "杀号筛选",
    "compound_selection": "复式组合",
    "frequency_window": "窗口频率",
    "recent_digit_exclusion": "上期号码排除",
    "group3_group6": "组三组六结构",
}


def atom_label(atom: str) -> str:
    return ATOM_LABELS.get(atom, atom)


def _method_phrase(atoms: list[str]) -> str:
    labels = [atom_label(x) for x in atoms[:2]]
    if not labels:
        return "基础规则"
    return " + ".join(labels)


def _title(lottery: str, play: str, atoms: list[str]) -> str:
    return f"{lottery}{play}技巧：用{_method_phrase(atoms)}一步步筛选号码"


def _secondary_keywords(lottery: str, play: str, atoms: list[str]) -> list[str]:
    values = [f"{lottery}技巧", f"{play}技巧", f"{lottery}{play}投注技巧"]
    values.extend(f"{lottery}{atom_label(a)}" for a in atoms[:3])
    out = []
    for value in values:
        if value not in out:
            out.append(value)
    return out


def _outline(play: str, atoms: list[str], case_ready: bool) -> list[str]:
    sections = [
        f"{play}怎么玩：先把投注规则说清楚",
        f"方法核心：{_method_phrase(atoms)}到底在计算什么",
        "按步骤筛选：从原始号码到候选号码",
    ]
    if case_ready:
        sections.append("简单案例：用一小段数据完整复算一次")
    else:
        sections.append("案例条件：先补齐缺失的技巧算法定义")
    sections.extend(["投注前校验：注数、位置和中奖条件", "容易误解的地方与风险说明"])
    return sections


def _case_structure(plan: dict) -> str:
    case_plan = plan.get("case_plan", {})
    metrics = [x.get("metric", "") for x in case_plan.get("supported", [])]
    selector = case_plan.get("resolved_selector") or plan.get("resolved_selector") or "unresolved"
    return f"selector={selector};metrics={','.join(metrics)};scope={plan.get('allowed_case_scope')}"


def _angle_key(plan: dict) -> str:
    subject_lottery = str(plan.get("subject_lottery") or plan.get("lottery") or "")
    subject_play = str(plan.get("subject_play") or plan.get("play") or "")
    selector = str(plan.get("resolved_selector") or plan.get("case_plan", {}).get("resolved_selector") or "")
    raw = "|".join([
        str(plan.get("provider_id") or ""), str(plan.get("lottery") or ""), str(plan.get("play") or ""),
        subject_lottery, subject_play,
        str(plan.get("technique_family") or ""), ",".join(sorted(plan.get("technique_atoms", []))),
        selector,
    ])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]


def blueprint_from_plan(plan: dict) -> dict:
    atoms = plan.get("technique_atoms", [])
    case_plan = plan.get("case_plan", {})
    rule_lottery = plan["lottery"]
    rule_play = plan["play"]
    subject_lottery = str(plan.get("subject_lottery") or rule_lottery)
    subject_play = str(plan.get("subject_play") or rule_play)
    title = _title(subject_lottery, subject_play, atoms)
    primary_keyword = primary_keyword_for(subject_lottery, subject_play, atoms)
    case_structure = _case_structure(plan)
    content_type = str(plan.get("content_type") or default_content_type())
    site_category_key = site_category_for(content_type)
    fp = fingerprint(
        plan.get("provider_id", ""), rule_lottery, rule_play,
        subject_lottery, subject_play,
        plan.get("technique_family", ""), " ".join(sorted(atoms)), case_structure,
    )
    status = "ready_for_draft"
    blockers: list[str] = []
    if plan.get("status") == "blocked_mechanics_verification":
        blockers.append("mechanics_not_verified")
    if not case_plan.get("case_engine_ready"):
        blockers.append("technique_case_semantics_incomplete")
    if blockers:
        status = "blocked"
    blueprint = {
        "blueprint_id": "BP-" + fp[:16],
        "article_id": "LCM-IDEA-" + fp[:16],
        "provider_id": plan.get("provider_id"),
        "lottery": rule_lottery,
        "play": rule_play,
        "subject_lottery": subject_lottery,
        "subject_play": subject_play,
        "content_type": content_type,
        "site_category_key": site_category_key,
        "technique_family": plan.get("technique_family"),
        "technique_atoms": atoms,
        "resolved_selector": case_plan.get("resolved_selector") or plan.get("resolved_selector"),
        "selector_basis": case_plan.get("selector_basis") or plan.get("selector_basis"),
        "source_positions": plan.get("positions", []),
        "angle_signature": plan.get("angle_signature") or _angle_key(plan),
        "title": title,
        "slug_seed": "-".join([subject_lottery, subject_play, *atoms[:2]]),
        "primary_keyword": primary_keyword,
        "secondary_keywords": _secondary_keywords(subject_lottery, subject_play, atoms),
        "search_intent": "学习具体投注技巧并看懂可复算案例",
        "information_gain_type": "method_mechanics_and_reproducible_case",
        "summary_goal": f"用简单中文解释{subject_play}中的{_method_phrase(atoms)}，并给出可复算案例。",
        "outline": _outline(subject_play, atoms, case_plan.get("case_engine_ready", False)),
        "case_structure": case_structure,
        "case_plan": case_plan,
        "case_scope": plan.get("allowed_case_scope"),
        "rule_refs": plan.get("rule_refs", []),
        "source_refs": plan.get("source_refs", []),
        "source_support_count": plan.get("source_support_count", 0),
        "source_risk_rate": plan.get("source_risk_rate", 0),
        "fingerprint": fp,
        "status": status,
        "blockers": blockers,
        "article_status": "idea",
        "editorial_contract_version": "1.0",
        "seo_requirements": {
            "plain_chinese": True,
            "example_required": True,
            "unique_information_gain_required": True,
            "unique_exact_primary_keyword_required": True,
            "avoid_keyword_stuffing": True,
            "avoid_guaranteed_outcomes": True,
        },
    }

    keyword_hits = keyword_owners(primary_keyword, exclude_article_id=blueprint["article_id"])
    blueprint["keyword_owner_hits"] = [
        {"article_id": row.get("article_id"), "primary_keyword": primary_keyword, "status": row.get("status")}
        for row in keyword_hits[:5]
    ]
    if keyword_hits:
        blueprint["status"] = "keyword_blocked"
        blueprint["blockers"].append("exact_primary_keyword_owned")

    duplicate_hits = duplicate_candidates(blueprint)
    blueprint["duplicate_hits"] = [
        {"article_id": h.article_id, "title": h.title, "score": h.score, "reason": h.reason}
        for h in duplicate_hits[:5]
    ]
    if duplicate_hits:
        blueprint["status"] = "duplicate_blocked"
        blueprint["blockers"].append("existing_article_overlap")

    structural_hits = structural_duplicate_candidates(blueprint)
    blueprint["structural_duplicate_hits"] = [
        {"article_id": h.article_id, "title": h.title, "score": h.score, "reasons": h.reasons}
        for h in structural_hits[:5]
    ]
    if structural_hits:
        blueprint["status"] = "duplicate_blocked"
        if "structural_method_overlap" not in blueprint["blockers"]:
            blueprint["blockers"].append("structural_method_overlap")
    return blueprint


def generate_blueprints(provider_id: str, lottery: str, play: str, count: int = 10) -> dict:
    plan_result = plan_articles(provider_id, lottery, play, max(count * 3, count))
    blueprints = []
    seen_fingerprints = set()
    for plan in plan_result.get("plans", []):
        bp = blueprint_from_plan(plan)
        if bp["fingerprint"] in seen_fingerprints:
            continue
        seen_fingerprints.add(bp["fingerprint"])
        blueprints.append(bp)
        if len(blueprints) >= count:
            break
    return {
        "provider_id": provider_id,
        "lottery": lottery,
        "play": play,
        "plan_status": plan_result.get("status"),
        "requested": count,
        "generated": len(blueprints),
        "ready": sum(x["status"] == "ready_for_draft" for x in blueprints),
        "blocked": sum(x["status"] != "ready_for_draft" for x in blueprints),
        "blueprints": blueprints,
    }
