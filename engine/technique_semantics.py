from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEMANTICS_FILE = ROOT / "knowledge" / "TECHNIQUE_SEMANTICS.json"


def load_semantics() -> dict:
    return json.loads(SEMANTICS_FILE.read_text(encoding="utf-8"))


def case_requirements(atoms: list[str]) -> dict:
    definitions = load_semantics().get("atoms", {})
    supported = []
    unsupported = []
    for atom in atoms:
        spec = definitions.get(atom)
        if not spec:
            unsupported.append(atom)
            continue
        supported.append({
            "atom": atom,
            "metric": spec.get("metric"),
            "definition": spec.get("definition"),
            "safe_article_use": spec.get("safe_article_use"),
        })
    return {
        "supported": supported,
        "unsupported": unsupported,
        "case_engine_ready": bool(supported) and not unsupported,
    }
