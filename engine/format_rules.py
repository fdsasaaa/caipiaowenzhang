from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "formats" / "dingma_rotation_v1.json"


@dataclass
class FormatReport:
    passed: bool
    syntax: str | None = None
    tokens: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    format_status: str | None = None


def load_format_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def _matches(label: str, requested: str) -> bool:
    if label == requested:
        return True
    return requested in [x.strip() for x in label.split("/")]


def find_format_rule(play_type: str, play_name: str) -> dict | None:
    for row in load_format_registry()["rules"]:
        if _matches(row["play_type"], play_type) and _matches(row["play_name"], play_name):
            return row
    return None


def _space_tokens(content: str) -> list[str]:
    return [x for x in content.strip().split() if x]


def _digit_pool(tokens: list[str]) -> bool:
    return bool(tokens) and all(len(x) == 1 and x.isdigit() for x in tokens)


def _fixed_digit_tokens(tokens: list[str], width: int) -> bool:
    return bool(tokens) and all(len(x) == width and x.isdigit() for x in tokens)


def _hyphen_digit_sets(content: str, count: int) -> tuple[bool, list[str]]:
    groups = content.strip().split("-")
    ok = len(groups) == count and all(g and g.isdigit() for g in groups)
    return ok, groups


def validate_format(play_type: str, play_name: str, content: str) -> FormatReport:
    row = find_format_rule(play_type, play_name)
    if not row:
        return FormatReport(False, errors=["no format rule for play_type + play_name"])
    syntax = row["syntax"]
    tokens = _space_tokens(content)
    errors: list[str] = []

    if syntax == "three_digit_tokens_space_separated":
        ok = _fixed_digit_tokens(tokens, 3)
    elif syntax == "three_digit_tokens_space_separated_exactly_one_pair":
        ok = _fixed_digit_tokens(tokens, 3) and all(sorted([t.count(d) for d in set(t)]) == [1, 2] for t in tokens)
    elif syntax == "three_digit_tokens_space_separated_all_distinct":
        ok = _fixed_digit_tokens(tokens, 3) and all(len(set(t)) == 3 for t in tokens)
    elif syntax == "two_digit_tokens_space_separated":
        ok = _fixed_digit_tokens(tokens, 2)
    elif syntax == "four_digit_tokens_space_separated":
        ok = _fixed_digit_tokens(tokens, 4)
    elif syntax == "five_digit_tokens_space_separated":
        ok = _fixed_digit_tokens(tokens, 5)
    elif syntax == "digit_pool_space_separated":
        ok = _digit_pool(tokens)
    elif syntax == "single_digit":
        ok = len(tokens) == 1 and _digit_pool(tokens)
    elif syntax == "sum_values_space_separated_keep_multidigit_atomic":
        ok = bool(tokens) and all(t.isdigit() for t in tokens)
    elif syntax == "three_position_digit_sets_hyphen_separated":
        ok, tokens = _hyphen_digit_sets(content, 3)
    elif syntax == "two_position_digit_sets_hyphen_separated":
        ok, tokens = _hyphen_digit_sets(content, 2)
    elif syntax == "four_position_digit_sets_hyphen_separated":
        ok, tokens = _hyphen_digit_sets(content, 4)
    elif syntax == "five_position_digit_sets_hyphen_separated":
        ok, tokens = _hyphen_digit_sets(content, 5)
    elif syntax == "combination_tokens_space_separated":
        ok = bool(tokens) and all(t.isdigit() for t in tokens)
    elif syntax == "two_tokens_space_separated":
        ok = tokens in (["龙", "虎"], ["虎", "龙"])
    else:
        return FormatReport(False, syntax=syntax, tokens=tokens, errors=["unsupported syntax parser"], format_status=row.get("format_status"))

    if not ok:
        errors.append(f"content does not match syntax {syntax}")
    return FormatReport(not errors, syntax=syntax, tokens=tokens, errors=errors, format_status=row.get("format_status"))
