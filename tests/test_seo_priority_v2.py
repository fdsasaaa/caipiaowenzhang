import json
from pathlib import Path

from engine.seo_priority import rank_blueprints, read_demand_signals, score_blueprint


def _bp(article_id, keyword, support=10, risk=0.1, status="ready_for_draft"):
    return {
        "article_id": article_id,
        "blueprint_id": "BP-" + article_id,
        "title": keyword + "：案例",
        "primary_keyword": keyword,
        "status": status,
        "blockers": [] if status == "ready_for_draft" else ["blocked_test"],
        "source_support_count": support,
        "source_risk_rate": risk,
        "information_gain_type": "method_mechanics_and_reproducible_case",
        "keyword_owner_hits": [],
        "duplicate_hits": [],
        "structural_duplicate_hits": [],
    }


def test_internal_only_ranking_prefers_more_support_and_lower_risk():
    low = _bp("A1", "分分彩跨度技巧", support=2, risk=0.7)
    high = _bp("A2", "分分彩遗漏技巧", support=50, risk=0.05)
    ranked = rank_blueprints([low, high])
    assert ranked[0]["article_id"] == "A2"
    assert ranked[0]["signal_mode"] == "internal_only"
    assert ranked[0]["priority_score"] > ranked[1]["priority_score"]


def test_blocked_blueprint_is_ineligible_even_with_huge_external_signal():
    bp = _bp("A3", "分分彩重复主题", status="duplicate_blocked")
    signal = {"primary_keyword": "分分彩重复主题", "source": "gsc", "impressions": 100000, "clicks": 5000, "position": 8}
    row = rank_blueprints([bp], [signal])[0]
    assert row["eligible"] is False
    assert row["priority_score"] == 0


def test_external_gsc_like_signal_boosts_matching_keyword():
    a = _bp("A4", "分分彩冷热技巧", support=10, risk=0.1)
    b = _bp("A5", "分分彩和值技巧", support=10, risk=0.1)
    signals = [{
        "query": "分分彩和值技巧",
        "source": "google_search_console",
        "impressions": 5000,
        "clicks": 30,
        "position": 11.0,
    }]
    ranked = rank_blueprints([a, b], signals)
    assert ranked[0]["article_id"] == "A5"
    assert ranked[0]["signal_mode"] == "external_augmented"
    assert any("external_impressions=5000" in x for x in ranked[0]["reasons"])


def test_signal_reader_accepts_jsonl(tmp_path: Path):
    path = tmp_path / "signals.jsonl"
    path.write_text(json.dumps({"query": "分分彩遗漏技巧", "source": "gsc", "impressions": 100}) + "\n", encoding="utf-8")
    rows = read_demand_signals(path)
    assert rows[0]["impressions"] == 100
