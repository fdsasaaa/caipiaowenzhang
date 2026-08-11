import hashlib
import json
from pathlib import Path

from engine.approval import evaluate_for_approval


ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / "smoke" / "batch1"
ARTICLE_IDS = [
    "LCM-SMOKE-20260811-01",
    "LCM-SMOKE-20260811-02",
    "LCM-SMOKE-20260811-03",
]


def load(kind: str, article_id: str) -> dict:
    return json.loads((BATCH / kind / f"{article_id}.json").read_text(encoding="utf-8"))


def test_smoke_batch1_passes_real_approval_pipeline():
    for article_id in ARTICLE_IDS:
        packet = load("packets", article_id)
        article = load("articles", article_id)
        expected = load("approved", article_id)

        assert article["content_hash"] == hashlib.sha256(article["content"].encode("utf-8")).hexdigest()
        assert article["site_category_key"] == "tzjq"
        assert article["content_format"] == "html"
        assert article["status"] == "draft"
        assert "格式演示，不代表实际开奖记录。" in article["content"]

        result = evaluate_for_approval(packet, article)
        assert result.approved, f"{article_id}: {result.errors}"
        assert result.status == "approved"
        assert result.quality_score >= 80
        assert result.publish_package is not None

        actual = result.publish_package
        for key, value in expected.items():
            if key == "approved_at":
                continue
            assert actual.get(key) == value, f"{article_id}: field {key} differs"

        assert actual["content_hash"] == expected["content_hash"]
        assert actual["status"] == "approved"
        assert actual["site_category_key"] == "tzjq"
        assert actual["content_format"] == "html"


def test_smoke_batch1_stays_out_of_publication_schedule():
    manifest = json.loads((BATCH / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["publication_policy"] == "draft_only_no_schedule_no_publish"
    for article_id in ARTICLE_IDS:
        approved = load("approved", article_id)
        assert "publish_at" not in approved
        assert approved["status"] == "approved"
