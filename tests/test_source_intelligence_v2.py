import json
from pathlib import Path

from engine.source_intelligence import build_knowledge_card, ingest_file


def test_good_source_becomes_rule_bound_knowledge_card():
    row = {
        "source_name": "fixture",
        "id": "1",
        "title": "分分彩后三跨度技巧：用近12期做演示",
        "content": "最近12期先统计后三跨度。例如开奖号码12345，可以计算后三345的跨度。这里只描述历史结构，不代表下一期一定会出。",
        "url": "https://example.test/1",
    }
    card = build_knowledge_card(row)
    assert card["quality"]["decision"] == "keep"
    assert "span_range" in card["technique_atoms"]
    assert "后三" in card["positions"]
    assert card["knowledge_status"] == "eligible_after_rule_binding"
    assert card["publishable"] is False


def test_reply_boilerplate_is_rejected():
    card = build_knowledge_card({"id": "2", "title": "冷号如何挑选", "content": "顶一下"})
    assert card["quality"]["decision"] == "reject"
    assert "reply_boilerplate" in card["quality"]["signals"]


def test_generic_printable_title_is_quarantined_or_rejected():
    card = build_knowledge_card({
        "id": "3",
        "title": "百瑞彩票论坛 - 彩票娱乐信息分享领导者!",
        "content": "小公举 2016-8-10 时时彩独胆算法之个位版",
    })
    assert card["quality"]["decision"] in {"quarantine", "reject"}
    assert "generic_or_printable_title" in card["quality"]["signals"]


def test_claims_keep_evidence_pointer_and_remain_unverified():
    content = "这个方法声称准确率95%。下一句只是普通说明。"
    card = build_knowledge_card({"id": "4", "title": "测试", "content": content})
    assert card["claims"]
    claim = card["claims"][0]
    assert claim["claim_type"] == "percentage_performance"
    assert claim["verification_status"] == "unverified_source_claim"
    assert claim["evidence"]["source_id"] == card["source_id"]
    assert "95%" in claim["evidence"]["snippet"]


def test_exact_duplicate_is_removed_during_file_ingestion(tmp_path: Path):
    body = (
        "最近20期观察个位遗漏，记录每个数字距离最近一次出现的期数作为研究样本。"
        "当某个号码遗漏达到3期时，只把它记入候选观察表，再结合下一步规则继续筛选。"
        "这只是历史数据整理案例，不代表遗漏越大下一期越容易出现。"
    )
    rows = [
        {"source_name": "x", "id": "a", "title": "遗漏技巧", "content": body},
        {"source_name": "x", "id": "b", "title": "另一标题", "content": body},
    ]
    src = tmp_path / "in.jsonl"
    src.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    out = tmp_path / "knowledge.jsonl"
    quarantine = tmp_path / "quarantine.jsonl"
    result = ingest_file(src, out, quarantine)
    assert result["input"] == 2
    assert result["knowledge_cards"] == 1
    qrows = [json.loads(line) for line in quarantine.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(qrows) == 1
    assert "exact_content_duplicate" in qrows[0]["quality"]["signals"]
