import pytest

from engine.site_contract import default_content_type, required_content_format, site_category_for


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
