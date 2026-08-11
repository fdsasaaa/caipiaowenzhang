from engine.v2_readiness import readiness_report


def test_v2_code_can_be_ready_without_external_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    report = readiness_report()
    assert report["v2_code_ready"] is True
    assert report["live_model_generation_ready"] is False
    assert report["seo_signal_mode"] == "internal_only"
    assert "live_model_api_key_not_configured" in report["blockers_or_external_dependencies"]
    assert "seo_priority_has_no_external_demand_signals" in report["blockers_or_external_dependencies"]


def test_api_key_only_changes_runtime_readiness_not_code_readiness(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-key")
    report = readiness_report()
    assert report["v2_code_ready"] is True
    assert report["live_model_generation_ready"] is True
    assert report["openai_api_key_configured"] is True
