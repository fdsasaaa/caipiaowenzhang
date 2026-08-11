from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

POSITION_INDEX = {"万位": 0, "千位": 1, "百位": 2, "十位": 3, "个位": 4}
WINDOW_INDEXES = {
    "前二": (0, 1),
    "后二": (3, 4),
    "前三": (0, 1, 2),
    "中三": (1, 2, 3),
    "后三": (2, 3, 4),
    "前四": (0, 1, 2, 3),
    "后四": (1, 2, 3, 4),
    "五星": (0, 1, 2, 3, 4),
}


def parse_draw(draw: str) -> tuple[int, ...]:
    if not isinstance(draw, str) or len(draw) != 5 or not draw.isdigit():
        raise ValueError("draw must be a five-digit decimal string")
    return tuple(int(ch) for ch in draw)


def extract(draw: str, selector: str) -> tuple[int, ...]:
    digits = parse_draw(draw)
    if selector in POSITION_INDEX:
        return (digits[POSITION_INDEX[selector]],)
    if selector in WINDOW_INDEXES:
        return tuple(digits[i] for i in WINDOW_INDEXES[selector])
    raise KeyError(f"unknown selector: {selector}")


def digit_sum(draw: str, selector: str) -> int:
    return sum(extract(draw, selector))


def span(draw: str, selector: str) -> int:
    values = extract(draw, selector)
    return max(values) - min(values)


def parity_pattern(draw: str, selector: str) -> str:
    return "".join("双" if x % 2 == 0 else "单" for x in extract(draw, selector))


def size_pattern(draw: str, selector: str) -> str:
    return "".join("小" if x <= 4 else "大" for x in extract(draw, selector))


def distinct_count(draw: str, selector: str) -> int:
    return len(set(extract(draw, selector)))


def repeat_pattern(draw: str, selector: str) -> str:
    values = extract(draw, selector)
    counts = sorted(Counter(values).values(), reverse=True)
    if len(values) == 3:
        if counts == [3]:
            return "豹子"
        if counts == [2, 1]:
            return "组三"
        if counts == [1, 1, 1]:
            return "组六"
    if len(values) == 2:
        return "重号" if counts == [2] else "两不同"
    return "-".join(str(x) for x in counts)


def has_neighbor_pair(draw: str, selector: str, circular: bool = False) -> bool:
    values = sorted(set(extract(draw, selector)))
    for a in values:
        for b in values:
            if a >= b:
                continue
            if abs(a - b) == 1:
                return True
            if circular and {a, b} == {0, 9}:
                return True
    return False


def frequency(draws: list[str], selector: str) -> dict[int, int]:
    counts = Counter()
    for draw in draws:
        counts.update(extract(draw, selector))
    return {d: counts.get(d, 0) for d in range(10)}


def position_frequency(draws: list[str], position: str) -> dict[int, int]:
    if position not in POSITION_INDEX:
        raise KeyError(position)
    return frequency(draws, position)


def current_omission(draws: list[str], position: str) -> dict[int, int]:
    """Consecutive draws since each digit last appeared at one fixed position.

    draws are chronological oldest -> newest. If a digit is in the latest draw,
    omission=0. If never seen in the provided sample, omission=len(draws).
    """
    if position not in POSITION_INDEX:
        raise KeyError(position)
    idx = POSITION_INDEX[position]
    parsed = [parse_draw(d) for d in draws]
    result: dict[int, int] = {}
    for digit in range(10):
        gap = len(parsed)
        for distance, row in enumerate(reversed(parsed)):
            if row[idx] == digit:
                gap = distance
                break
        result[digit] = gap
    return result


@dataclass(frozen=True)
class WindowSnapshot:
    draw: str
    selector: str
    values: tuple[int, ...]
    sum_value: int
    span_value: int
    parity: str
    size: str
    distinct: int
    repeat: str
    has_neighbor: bool


def snapshot(draw: str, selector: str) -> WindowSnapshot:
    values = extract(draw, selector)
    return WindowSnapshot(
        draw=draw,
        selector=selector,
        values=values,
        sum_value=sum(values),
        span_value=max(values) - min(values),
        parity=parity_pattern(draw, selector),
        size=size_pattern(draw, selector),
        distinct=len(set(values)),
        repeat=repeat_pattern(draw, selector),
        has_neighbor=has_neighbor_pair(draw, selector),
    )
