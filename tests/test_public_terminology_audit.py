from __future__ import annotations

from pathlib import Path

from engine.public_terminology import audit_article, audit_repository


ROOT = Path(__file__).resolve().parents[1]


def test_committed_reader_articles_follow_ffc_terminology_policy():
    report = audit_repository(ROOT)
    assert report.scanned_files >= 16
    assert report.ffc_articles >= 16
    assert report.passed is True, report.as_dict()
    assert report.findings == []


def test_internal_taxonomy_field_does_not_count_as_reader_facing_leak():
    article = {
        "article_id": "A-1",
        "lottery": "时时彩",
        "subject_lottery": "分分彩",
        "title": "分分彩后三技巧",
        "seo_title": "分分彩后三技巧",
        "meta_description": "分分彩案例",
        "primary_keyword": "分分彩后三技巧",
        "summary": "分分彩复算案例",
        "tags": ["分分彩"],
        "content": "<p>分分彩正文。</p>",
    }
    assert audit_article("sample.json", article) == []


def test_unqualified_legacy_term_in_reader_fields_is_rejected():
    article = {
        "article_id": "A-2",
        "subject_lottery": "分分彩",
        "title": "时时彩后三技巧",
        "seo_title": "分分彩后三技巧",
        "meta_description": "分分彩案例",
        "primary_keyword": "分分彩后三技巧",
        "summary": "分分彩复算案例",
        "tags": ["分分彩"],
        "content": "<p>时时彩后三按和值筛选。</p>",
    }
    findings = audit_article("sample.json", article)
    assert {row.field for row in findings} == {"title", "content"}


def test_explicit_historical_source_term_is_allowed_in_body_only():
    article = {
        "article_id": "A-3",
        "subject_lottery": "分分彩",
        "title": "分分彩后三技巧",
        "seo_title": "分分彩后三技巧",
        "meta_description": "分分彩案例",
        "primary_keyword": "分分彩后三技巧",
        "summary": "分分彩复算案例",
        "tags": ["分分彩"],
        "content": "<p>历史规则库内部仍使用 时时彩 作为 mechanics 分类名，本文读者显示统一使用分分彩。</p>",
    }
    assert audit_article("sample.json", article) == []
