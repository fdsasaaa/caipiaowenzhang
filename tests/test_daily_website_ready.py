from datetime import datetime, timezone

from engine.daily_website_ready import (
    _keyword_allowed,
    load_daily_policy,
    production_date,
    public_safety_errors,
)


def test_daily_policy_volume_band():
    policy = load_daily_policy()
    assert policy["minimum"] == 10
    assert policy["target"] == 20
    assert policy["maximum"] == 25
    assert policy["candidate_pool"] >= policy["target"]
    assert policy["quality_floor_may_be_lowered"] is False
    assert policy["public_release_required_to_count"] is True


def test_production_date_uses_singapore_boundary():
    instant = datetime(2026, 8, 14, 17, 30, tzinfo=timezone.utc)
    assert production_date(instant, "Asia/Singapore") == "2026-08-15"


def test_broad_and_funding_keywords_are_blocked():
    policy = load_daily_policy()
    assert not _keyword_allowed("分分彩", policy)
    assert not _keyword_allowed("分分彩高级倍投实战", policy)
    assert not _keyword_allowed("分分彩资金管理方法", policy)
    assert _keyword_allowed("分分彩后二直选位置关系研究", policy)


def test_public_safety_gate_rejects_operational_instructions():
    policy = load_daily_policy()
    package = {
        "article_id": "x",
        "primary_keyword": "分分彩后二直选位置关系研究",
        "seo_title": "分分彩后二直选位置关系研究：结构复盘",
        "content": (
            "<h2>机制</h2><p>这是研究说明。</p>"
            "<h2>操作</h2><p>下一期选1、2、3，然后加倍。</p>"
            "<h2>边界</h2><p>随机波动不能单独证明未来预测优势。</p>" + "研究记录。" * 100
        ),
        "content_hash": "new",
        "parent_content_hash": "old",
    }
    errors = public_safety_errors(package, policy)
    assert any(item.startswith("operational_pattern:") for item in errors)


def test_public_safety_gate_accepts_non_operational_research_copy(monkeypatch):
    policy = load_daily_policy()
    monkeypatch.setattr("engine.daily_website_ready.audit_article", lambda *_: [])
    package = {
        "article_id": "x",
        "primary_keyword": "分分彩后二直选位置关系研究",
        "seo_title": "分分彩后二直选位置关系研究：结构与验证边界",
        "content": (
            "<h2>结构</h2><p>本文只解释位置关系的分类方法和记录方式。</p>"
            "<h2>验证</h2><p>参数应先登记，再使用独立样本复核。</p>"
            "<h2>边界</h2><p>短期结果存在随机波动，结构分类不能单独证明未来预测优势。</p>"
            + "研究时应保存规则版本、样本边界和复核记录。" * 45
        ),
        "content_hash": "new",
        "parent_content_hash": "old",
    }
    assert public_safety_errors(package, policy) == []
