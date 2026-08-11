import json
from pathlib import Path

from scripts.normalize_search_console_csv import normalize_csv


def test_normalize_english_search_console_csv(tmp_path: Path):
    src = tmp_path / "gsc.csv"
    src.write_text(
        "Top queries,Clicks,Impressions,CTR,Position\n"
        "分分彩遗漏技巧,30,5000,0.6%,11.2\n",
        encoding="utf-8",
    )
    out = tmp_path / "signals.jsonl"
    result = normalize_csv(src, out)
    assert result["signals"] == 1
    row = json.loads(out.read_text(encoding="utf-8").strip())
    assert row["query"] == "分分彩遗漏技巧"
    assert row["source"] == "google_search_console"
    assert row["clicks"] == 30.0
    assert row["impressions"] == 5000.0
    assert row["ctr"] == 0.006
    assert row["position"] == 11.2


def test_normalize_chinese_search_console_headers(tmp_path: Path):
    src = tmp_path / "gsc-cn.csv"
    src.write_text("查询,点击次数,展示次数,点击率,平均排名\n分分彩和值技巧,5,800,1.25%,18\n", encoding="utf-8")
    out = tmp_path / "signals.jsonl"
    normalize_csv(src, out)
    row = json.loads(out.read_text(encoding="utf-8").strip())
    assert row["query"] == "分分彩和值技巧"
    assert row["ctr"] == 0.0125
