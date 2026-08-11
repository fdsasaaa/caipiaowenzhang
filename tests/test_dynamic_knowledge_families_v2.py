import json
from pathlib import Path

from engine import planner
from engine.knowledge_families_v2 import build_dynamic_families, write_dynamic_families


def _card(source_id, position, risk=0):
    return {
        "source_id": source_id,
        "quality": {"decision": "keep"},
        "knowledge_status": "eligible_after_rule_binding",
        "technique_atoms": ["omission_threshold", "position_filter"],
        "positions": [position],
        "lotteries": ["时时彩"],
        "topic_tags": ["定位胆", "遗漏"],
        "classification": "定位胆",
        "claim_risk_max": risk,
    }


def test_cards_with_same_atoms_form_one_dynamic_family():
    families = build_dynamic_families([_card("S1", "个位", 0), _card("S2", "十位", 90)])
    assert len(families) == 1
    family = families[0]
    assert family["source_count"] == 2
    assert family["risk_rate"] == 0.5
    assert family["positions"] == ["个位", "十位"]
    assert family["example_source_ids"] == ["S1", "S2"]
    assert family["origin"] == "dynamic_source_intelligence_v2"


def test_planner_reads_dynamic_family_and_emits_source_refs(monkeypatch, tmp_path: Path):
    cards = tmp_path / "cards.jsonl"
    cards.write_text(json.dumps(_card("NEWSRC-1", "个位"), ensure_ascii=False) + "\n", encoding="utf-8")
    dynamic_dir = tmp_path / "dynamic_families"
    dynamic_file = dynamic_dir / "incoming.jsonl"
    write_dynamic_families(cards, dynamic_file)

    empty_clusters = tmp_path / "clusters.jsonl"
    empty_clusters.write_text("", encoding="utf-8")
    articles = tmp_path / "articles.jsonl"
    articles.write_text("", encoding="utf-8")

    monkeypatch.setattr(planner, "DYNAMIC_FAMILIES", dynamic_dir)
    monkeypatch.setattr(planner, "CLUSTERS", empty_clusters)
    monkeypatch.setattr(planner, "ARTICLES", articles)
    monkeypatch.setattr(planner, "iter_brbcw_families", lambda: iter([]))
    monkeypatch.setattr(planner, "rule_capability", lambda provider, lottery, play: {
        "mechanics_verified": True,
        "economics_verified": False,
        "mechanics_rule_refs": ["M1"],
        "economics_rule_refs": [],
    })

    result = planner.plan_articles("historical", "时时彩", "定位胆", 10)
    assert result["knowledge_sources"]["dynamic_families"] == 1
    assert result["plans"]
    plan = result["plans"][0]
    assert plan["knowledge_origin"] == "dynamic_source_intelligence_v2"
    assert plan["source_refs"] == ["NEWSRC-1"]
    assert plan["source_support_count"] == 1
