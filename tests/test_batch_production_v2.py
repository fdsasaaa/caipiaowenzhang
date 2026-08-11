from types import SimpleNamespace

from engine import batch_production_v2


def _bp(article_id, atoms, selector, metrics, play="后三直选"):
    return {
        "article_id": article_id,
        "blueprint_id": "BP-" + article_id,
        "status": "ready_for_draft",
        "subject_lottery": "分分彩",
        "subject_play": play,
        "content_type": "technique_article",
        "technique_atoms": atoms,
        "case_structure": f"selector={selector};metrics={metrics};scope=mechanics_only",
    }


def test_batch_selector_skips_same_batch_structural_overlap():
    first = {"article_id": "A1", "eligible": True, "blueprint": _bp("A1", ["position_filter", "span_range"], "后三", "position_filter,span")}
    duplicate = {"article_id": "A2", "eligible": True, "blueprint": _bp("A2", ["span_range", "position_filter"], "后三", "span,position_filter")}
    different = {"article_id": "A3", "eligible": True, "blueprint": _bp("A3", ["omission_threshold"], "个位", "omission", play="定位胆")}
    selected, skipped = batch_production_v2.select_nonoverlapping_topics([first, duplicate, different], 2)
    assert [x["article_id"] for x in selected] == ["A1", "A3"]
    assert any(x["article_id"] == "A2" and x["reason"] == "same_batch_structural_overlap" for x in skipped)


def test_produce_ranked_batch_runs_generation_then_approval(monkeypatch):
    blueprint = _bp("A4", ["omission_threshold"], "个位", "omission", play="定位胆")
    ranking = {
        "signal_mode": "internal_only",
        "ranked": [{
            "article_id": "A4",
            "eligible": True,
            "priority_score": 78.0,
            "priority_band": "high",
            "signal_mode": "internal_only",
            "blueprint": blueprint,
        }],
    }
    packet = {"article_id": "A4", "status": "ready_for_ai_draft"}
    article = {"article_id": "A4", "status": "draft"}
    package = {"article_id": "A4", "status": "approved"}

    monkeypatch.setattr(batch_production_v2, "rank_generated_topics", lambda *args, **kwargs: ranking)
    monkeypatch.setattr(batch_production_v2, "build_draft_packet", lambda bp: packet)
    monkeypatch.setattr(batch_production_v2, "generate_article", lambda *args, **kwargs: SimpleNamespace(article=article, provider="fake", model="fake-model", response_id="r1"))
    monkeypatch.setattr(batch_production_v2, "evaluate_for_approval", lambda p, a: SimpleNamespace(approved=True, status="approved", quality_score=95, errors=[], warnings=[], registry_record={"article_id":"A4"}, publish_package=package))

    result = batch_production_v2.produce_ranked_batch("p", "时时彩", "定位胆", count=1, api_key="fake")
    assert result["selected"] == 1
    assert result["generated"] == 1
    assert result["approved"] == 1
    assert result["results"][0]["approved_package"] == package
