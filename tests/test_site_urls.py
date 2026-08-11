import pytest

from engine.site_urls import validate_published_url


def test_friendly_and_native_cms_urls_are_allowed():
    assert validate_published_url("https://www.laocaimi.org/article/example") == "https://www.laocaimi.org/article/example"
    assert validate_published_url("https://www.laocaimi.org/index.php?c=show&id=321") == "https://www.laocaimi.org/index.php?c=show&id=321"
    assert validate_published_url("https://laocaimi.org/index.php?id=321&c=show") == "https://laocaimi.org/index.php?id=321&c=show"


@pytest.mark.parametrize(
    "url, message",
    [
        ("http://www.laocaimi.org/article/a", "must use https"),
        ("https://evil.example/article/a", "host is not allowed"),
        ("https://user:pass@www.laocaimi.org/article/a", "must not contain credentials"),
        ("https://www.laocaimi.org:444/article/a", "non-HTTPS port"),
        ("https://www.laocaimi.org/", "concrete article path"),
        ("https://www.laocaimi.org/article/a#part", "must not contain fragment"),
        ("https://www.laocaimi.org/article/a?ref=x", "query is allowed only"),
        ("https://www.laocaimi.org/index.php?c=show&id=321&ref=x", "exactly c and id"),
        ("https://www.laocaimi.org/index.php?c=show&c=show&id=321", "exactly c and id once"),
        ("https://www.laocaimi.org/index.php?c=list&id=321", "exactly c=show and id"),
        ("https://www.laocaimi.org/index.php?c=show&id=0", "invalid id"),
        ("https://www.laocaimi.org/index.php?c=show&id=0321", "invalid id"),
    ],
)
def test_invalid_or_noncanonical_urls_are_rejected(url, message):
    with pytest.raises(ValueError, match=message):
        validate_published_url(url)
