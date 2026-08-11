import json
from itertools import combinations
from pathlib import Path

from engine.ai_generation import validate_generated_identity
from engine.approval import evaluate_for_approval
from engine.claim_evidence import audit_claim_evidence
from engine.draft_packets import build_draft_packet

ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = ROOT / "agent" / "results" / "v2-quality-smoke-002"


def _load(name: str) -> dict:
    return json.loads((CASE_DIR / name).read_text(encoding="utf-8"))


def test_v21_quality_smoke_002_distinguishes_bet_count_from_ordered_coverage():
    blueprint = _load("blueprint.json")
    article = _load("article.json")
    packet = build_draft_packet(blueprint)

    assert packet["editorial_contract_version"] == "1.0"
    assert packet["case_bundle"]["selector"] == "后二"

    digits = [0, 8, 9]
    unordered_pairs = list(combinations(digits, 2))
    assert unordered_pairs == [(0, 8), (0, 9), (8, 9)]
    assert len(unordered_pairs) == 3

    ordered_outcomes = {
        (a, b)
        for a, b in unordered_pairs
        for a, b in ((a, b), (b, a))
    }
    assert ordered_outcomes == {(0, 8), (8, 0), (0, 9), (9, 0), (8, 9), (9, 8)}
    assert len(ordered_outcomes) == 6

    all_group_bets = list(combinations(range(10), 2))
    assert len(all_group_bets) == 45
    assert len(ordered_outcomes) / 100 == 0.06
    assert round(len(unordered_pairs) / len(all_group_bets) * 100, 2) == 6.67

    validate_generated_identity(packet, article)

    evidence = audit_claim_evidence(packet, article)
    assert evidence.passed, evidence.errors

    result = evaluate_for_approval(packet, article)
    assert result.approved, result.errors
    assert result.quality_score == 100
    assert result.editorial_score == 100
    assert result.publish_package is not None
    assert result.publish_package["primary_keyword"] == "分分彩后二组选复式技巧"
    assert result.publish_package["practical_guidance"]["starting_space"].startswith("100")
