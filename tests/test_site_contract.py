import pytest

from engine.site_contract import (
    allowed_seo_cluster_ids,
    default_content_type,
    normalize_seo_cluster_assignment,
    required_content_format,
    seo_cluster_article_category_key,
    site_category_for,
)


def test_current_generator_maps_technique_articles_to_tzjq():
    assert default_content_type() == "technique_article"
    assert site_category_for("technique_article") == "tzjq"
    assert required_content_format() == "html"


def test_other_registered_content_types_are_explicit():
    assert site_category_for("hangup_scheme") == "gjfa"
    assert site_category_for("resource_article") == "zyyy"
    assert site_category_for("seo_topic") == "tzjq"


def test_unknown_content_type_fails_closed():
    with pytest.raises(LookupError):
        site_category_for("unknown_type")


def test_seo_cluster_contract_is_explicit_and_tzjq_scoped():
    assert seo_cluster_article_category_key() == "tzjq"
    assert set(allowed_seo_cluster_ids()) == {
        "ffc_research", "hash_ffc", "qiqu_ffc", "ssc", "racing", "platform_review", "research_lab"
    }
    assert normalize_seo_cluster_assignment("ssc", ["research_lab"]) == ("ssc", ["research_lab"])
    assert normalize_seo_cluster_assignment(None, None) == (None, [])


def test_invalid_seo_cluster_assignments_fail_closed():
    with pytest.raises(ValueError, match="unknown primary"):
        normalize_seo_cluster_assignment("made_up", [])
    with pytest.raises(ValueError, match="require a primary"):
        normalize_seo_cluster_assignment(None, ["ssc"])
    with pytest.raises(ValueError, match="duplicate secondary"):
        normalize_seo_cluster_assignment("ssc", ["research_lab", "research_lab"])
    with pytest.raises(ValueError, match="must not repeat"):
        normalize_seo_cluster_assignment("ssc", ["ssc"])
