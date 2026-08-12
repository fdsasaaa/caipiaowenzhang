from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.produce_articles_total import _provider_transport_from_environment

ROOT = Path(__file__).resolve().parents[1]


def test_production_controller_script_help_runs_from_repo_root():
    result = subprocess.run(
        [sys.executable, "scripts/produce_articles_total.py", "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Article Production Controller" in result.stdout


def test_controller_uses_configured_compatible_provider_transport(monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "https://provider.example/v1/")
    transport, base_url = _provider_transport_from_environment()
    assert callable(transport)
    assert base_url == "https://provider.example/v1"


def test_controller_keeps_default_openai_transport_without_base_url(monkeypatch):
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    transport, base_url = _provider_transport_from_environment()
    assert transport is None
    assert base_url is None
