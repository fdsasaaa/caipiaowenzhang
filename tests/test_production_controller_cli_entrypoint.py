from __future__ import annotations

import subprocess
import sys
from pathlib import Path

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
