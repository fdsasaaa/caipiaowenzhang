from __future__ import annotations

from itertools import product


def ordered_decimal_space(width: int) -> set[str]:
    if not isinstance(width, int) or width <= 0:
        raise ValueError("width must be a positive integer")
    return {"".join(chars) for chars in product("0123456789", repeat=width)}


def expand_direct_tokens(width: int, tokens: list[str] | tuple[str, ...] | set[str]) -> set[str]:
    if not isinstance(width, int) or width <= 0:
        raise ValueError("width must be a positive integer")
    out: set[str] = set()
    for token in tokens:
        value = str(token)
        if len(value) != width or not value.isdigit():
            raise ValueError(f"invalid {width}-digit direct token: {value!r}")
        out.add(value)
    return out


def expand_located_digits(width: int, position_index: int, digits: list[int | str] | tuple[int | str, ...] | set[int | str]) -> set[str]:
    if not isinstance(width, int) or width <= 0:
        raise ValueError("width must be a positive integer")
    if not isinstance(position_index, int) or not 0 <= position_index < width:
        raise ValueError("position_index out of range")
    digit_set = {str(x) for x in digits}
    if not digit_set or any(len(x) != 1 or not x.isdigit() for x in digit_set):
        raise ValueError("digits must contain one or more decimal digits")
    return {outcome for outcome in ordered_decimal_space(width) if outcome[position_index] in digit_set}


def normalized_direct_bet(*, bet_id: str, draw_id: str, lottery_id: str, play_id: str, width: int, tokens: list[str], stake_amount: float, prize_amount: float, target_space_id: str, phase_amounts: dict[str, float] | None = None) -> dict:
    row = {
        "bet_id": bet_id,
        "draw_id": draw_id,
        "lottery_id": lottery_id,
        "play_id": play_id,
        "target_space_id": target_space_id,
        "target_space_size": 10 ** width,
        "covered_outcomes": sorted(expand_direct_tokens(width, tokens)),
        "stake_amount": float(stake_amount),
        "prize_amount": float(prize_amount),
        "mapping_ref": "ordered_decimal_direct_v1",
    }
    if phase_amounts:
        row["phase_amounts"] = phase_amounts
    return row


def normalized_located_bet(*, bet_id: str, draw_id: str, lottery_id: str, play_id: str, width: int, position_index: int, digits: list[int | str], stake_amount: float, prize_amount: float, target_space_id: str, phase_amounts: dict[str, float] | None = None) -> dict:
    row = {
        "bet_id": bet_id,
        "draw_id": draw_id,
        "lottery_id": lottery_id,
        "play_id": play_id,
        "target_space_id": target_space_id,
        "target_space_size": 10 ** width,
        "covered_outcomes": sorted(expand_located_digits(width, position_index, digits)),
        "stake_amount": float(stake_amount),
        "prize_amount": float(prize_amount),
        "mapping_ref": "ordered_decimal_located_v1",
    }
    if phase_amounts:
        row["phase_amounts"] = phase_amounts
    return row
