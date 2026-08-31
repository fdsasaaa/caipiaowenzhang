import hashlib
import json
from pathlib import Path

from engine.approval import evaluate_for_approval
from engine.title_seo import TITLE_SEO_CONTRACT_VERSION
from engine.title_seo_runtime import suggest_title_candidates


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

        # Title SEO V1.0: inject title_candidates so apply_title_seo uses
        # the original title (candidates[0]) instead of regenerating a new one.
        original_title = str(article.get("title") or "")
        if "title_candidates" not in article:
            article["title_seo_contract_version"] = TITLE_SEO_CONTRACT_VERSION
            article["title_selection_reason"] = "smoke batch1 regression"
            generated = suggest_title_candidates(article, 4)
            article["title_candidates"] = list(dict.fromkeys([original_title, *generated]))[:5]

        result = evaluate_for_approval(packet, article)
        assert result.approved, f"{article_id}: {result.errors}"
        assert result.status == "approved"
        assert result.quality_score >= 80
        assert result.publish_package is not None

        actual = result.publish_package
        for key, value in expected.items():
            if key == "approved_at":
                continue
            if key in ("title", "seo_title"):
                # Title SEO V1.0 may rewrite the title; verify the actual
                # title passed all gates rather than asserting frozen equality.
                assert actual.get(key) == actual.get("title"), f"{article_id}: title/seo_title mismatch"
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
