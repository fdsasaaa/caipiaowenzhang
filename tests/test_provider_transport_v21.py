import json

import pytest

from engine.ai_generation import GenerationError
from engine.provider_transport import normalize_base_url, responses_endpoint
from scripts.model_provider_preflight_v21 import _model_ids, _pick_model, _structured_payload


def test_custom_https_base_url_normalizes_and_builds_responses_endpoint():
    assert normalize_base_url("https://example.test/v1/") == "https://example.test/v1"
    assert responses_endpoint("https://example.test/v1/") == "https://example.test/v1/responses"


def test_remote_http_base_url_is_rejected():
    with pytest.raises(GenerationError):
        normalize_base_url("http://example.test/v1")


def test_credentials_query_and_fragment_are_rejected():
    for value in (
        "https://user:pass@example.test/v1",
        "https://example.test/v1?token=x",
        "https://example.test/v1#frag",
    ):
        with pytest.raises(GenerationError):
            normalize_base_url(value)


def test_preflight_prefers_low_cost_looking_model_when_unspecified():
    payload = {"data": [{"id": "gpt-large"}, {"id": "gpt-mini"}, {"id": "other"}]}
    models = _model_ids(payload)
    assert _pick_model(models, None) == "gpt-mini"
    assert _pick_model(models, "explicit-model") == "explicit-model"


def test_preflight_uses_strict_structured_output_schema():
    payload = _structured_payload("test-model")
    assert payload["store"] is False
    assert payload["max_output_tokens"] == 64
    fmt = payload["text"]["format"]
    assert fmt["type"] == "json_schema"
    assert fmt["strict"] is True
    assert fmt["schema"]["additionalProperties"] is False
    assert fmt["schema"]["required"] == ["ok"]
