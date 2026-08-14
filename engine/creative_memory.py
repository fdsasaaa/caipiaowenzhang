from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from .dedup import LEXICAL_DUPLICATE_THRESHOLD, lexical_similarity
from .semantic_dedup import STRUCTURAL_DUPLICATE_THRESHOLD, structural_similarity
from .store import ROOT, iter_registry

APPROVED_ROOT = ROOT / "articles" / "approved"
ACTIVE_STATUSES = {"approved", "queued", "scheduled", "published", "draft", "idea"}

STYLE_DNA = (
    {"id": "case_first", "voice": "先给案例，再拆原理", "opening": "直接从一个具体号码或小例子开始", "bias": "少标题、强复算"},
    {"id": "question_first", "voice": "像和读者对话", "opening": "用一个真正值得回答的问题开场", "bias": "问答感、短段落"},
    {"id": "lab_note", "voice": "研究笔记", "opening": "先写本次只研究什么", "bias": "克制、实验感"},
    {"id": "myth_bust", "voice": "纠正常见误区", "opening": "先指出一种容易混淆的做法", "bias": "先错后对"},
    {"id": "comparison", "voice": "对比讲解", "opening": "先摆出两种容易混在一起的方法", "bias": "边比较边解释"},
    {"id": "micro_story", "voice": "轻故事化", "opening": "从一次纸上推演或观察切入", "bias": "有画面但不夸张"},
    {"id": "calculation_first", "voice": "算式驱动", "opening": "先给一个两三步能算清的关系", "bias": "数字清楚、文字简洁"},
    {"id": "reverse_reasoning", "voice": "逆向推理", "opening": "先说不研究什么，再说明为什么换角度", "bias": "反常识但不标题党"},
    {"id": "teacher_board", "voice": "像在白板上讲", "opening": "先定义一个最小概念", "bias": "逐步展开"},
    {"id": "reader_challenge", "voice": "邀请读者自己复算", "opening": "先抛一个可以马上动手验证的小任务", "bias": "参与感"},
    {"id": "minimal", "voice": "极简教程", "opening": "一句话进入主题", "bias": "删掉所有空泛铺垫"},
    {"id": "research_log", "voice": "过程记录", "opening": "交代这次尝试如何形成", "bias": "强调过程和边界"},
    {"id": "analogy", "voice": "轻类比", "opening": "用简单空间、距离、分组或网格类比解释", "bias": "易懂但不幼稚"},
    {"id": "mistake_first", "voice": "从错误动作切入", "opening": "先写最容易做错的一步", "bias": "实用、直接"},
    {"id": "two_layer", "voice": "先结论后理由", "opening": "先给方法核心，再补为什么", "bias": "阅读速度快"},
    {"id": "field_note", "voice": "老玩家观察笔记", "opening": "从执行纪律而不是玄学开场", "bias": "经验感、不过度权威"},
)


def _load_json(path: Path) -> dict | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _compact(record: dict) -> dict:
    return {
        "article_id": record.get("article_id"),
        "title": record.get("title"),
        "primary_keyword": record.get("primary_keyword"),
        "subject_lottery": record.get("subject_lottery") or record.get("lottery"),
        "subject_play": record.get("subject_play") or record.get("play"),
        "technique_atoms": list(record.get("technique_atoms") or []),
        "search_intent": record.get("search_intent"),
        "summary": record.get("summary"),
        "creator_style_id": record.get("creator_style_id"),
        "creator_novelty_summary": record.get("creator_novelty_summary"),
    }


def formal_inventory_records(root: Path | None = None) -> list[dict]:
    root = root or APPROVED_ROOT
    rows: dict[str, dict] = {}
    if root.exists():
        for path in sorted(root.glob("*.json")):
            value = _load_json(path)
            if not value or value.get("status") != "approved" or not value.get("article_id"):
                continue
            rows[str(value["article_id"])] = dict(value)
    for row in iter_registry("articles"):
        article_id = str(row.get("article_id") or "")
        if not article_id or str(row.get("status") or "") not in ACTIVE_STATUSES:
            continue
        rows.setdefault(article_id, dict(row))
    return list(rows.values())


def select_style_dna(seed: str) -> dict:
    digest = hashlib.sha256(str(seed).encode("utf-8")).digest()
    return dict(STYLE_DNA[int.from_bytes(digest[:2], "big") % len(STYLE_DNA)])


def build_long_term_memory_snapshot(*, representative_limit: int = 60, coverage_limit: int = 120) -> dict:
    records = formal_inventory_records()
    compact = [_compact(row) for row in records]
    play_counts = Counter(str(row.get("subject_play") or "") for row in compact if row.get("subject_play"))
    atom_counts = Counter(
        str(atom)
        for row in compact
        for atom in (row.get("technique_atoms") or [])
        if str(atom).strip()
    )

    signatures: list[str] = []
    seen_signatures: set[str] = set()
    for row in compact:
        play = str(row.get("subject_play") or "").strip()
        atoms = "+".join(sorted(str(x) for x in row.get("technique_atoms") or [] if str(x).strip()))
        signature = f"{play}::{atoms}" if play or atoms else ""
        if signature and signature not in seen_signatures:
            seen_signatures.add(signature)
            signatures.append(signature)

    representatives: list[dict] = []
    if compact and representative_limit > 0:
        ordered = sorted(compact, key=lambda row: str(row.get("article_id") or ""))
        if len(ordered) <= representative_limit:
            representatives = ordered
        else:
            step = (len(ordered) - 1) / max(1, representative_limit - 1)
            picked: set[int] = set()
            for i in range(representative_limit):
                idx = round(i * step)
                if idx not in picked:
                    picked.add(idx)
                    representatives.append(ordered[idx])

    return {
        "article_count": len(compact),
        "play_counts": dict(sorted(play_counts.items())),
        "top_technique_atoms": atom_counts.most_common(80),
        "coverage_signatures": signatures[:coverage_limit],
        "representative_articles": representatives,
        "memory_role": "avoid substantive repetition and encourage new combinations; never use as templates",
    }


def formal_inventory_duplicate_hits(candidate: dict) -> list[dict]:
    article_id = str(candidate.get("article_id") or "")
    hits: list[dict] = []
    for old in formal_inventory_records():
        if article_id and str(old.get("article_id") or "") == article_id:
            continue
        reasons: list[str] = []
        if candidate.get("primary_keyword") and candidate.get("primary_keyword") == old.get("primary_keyword"):
            reasons.append("same_primary_keyword")
        if candidate.get("slug") and candidate.get("slug") == old.get("slug"):
            reasons.append("same_slug")
        if candidate.get("content_hash") and candidate.get("content_hash") == old.get("content_hash"):
            reasons.append("same_content_hash")
        lexical = lexical_similarity(candidate, old)
        structural, structural_reasons = structural_similarity(candidate, old)
        if lexical >= LEXICAL_DUPLICATE_THRESHOLD:
            reasons.append(f"lexical={lexical:.3f}")
        if structural >= STRUCTURAL_DUPLICATE_THRESHOLD:
            reasons.append(f"structural={structural:.3f}")
        if reasons:
            hits.append({
                "article_id": old.get("article_id"),
                "title": old.get("title"),
                "lexical": lexical,
                "structural": structural,
                "reasons": reasons + structural_reasons,
            })
    return sorted(hits, key=lambda row: max(float(row["lexical"]), float(row["structural"])), reverse=True)


def creator_memory_metadata(request: dict, manifest: dict) -> dict:
    return {
        "creator_style_id": (request.get("style_dna") or {}).get("id"),
        "creator_novelty_summary": manifest.get("originality_note"),
        "creator_technique_memory": {
            "technique_name": manifest.get("technique_name"),
            "technique_tags": list(manifest.get("technique_tags") or []),
            "reader_value": manifest.get("reader_value"),
            "creation_mode": manifest.get("creation_mode"),
            "bankroll_design_summary": manifest.get("bankroll_design_summary"),
            "staking_design_summary": manifest.get("staking_design_summary"),
        },
    }
