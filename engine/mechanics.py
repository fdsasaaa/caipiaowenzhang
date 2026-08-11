from __future__ import annotations


def _digits(value: str, length: int) -> tuple[int, ...]:
    if not isinstance(value, str) or len(value) != length or not value.isdigit():
        raise ValueError(f"expected {length}-digit decimal string")
    return tuple(int(ch) for ch in value)


def direct_hit(bet: str, draw: str) -> bool:
    """Ordered positional match. bet and draw must have the same length."""
    if len(bet) != len(draw):
        raise ValueError("bet and draw length must match")
    return _digits(bet, len(bet)) == _digits(draw, len(draw))


def group2_hit(pair: tuple[int, int], draw2: str) -> bool:
    a, b = pair
    if a == b or any(x < 0 or x > 9 for x in pair):
        raise ValueError("group2 requires two distinct digits 0..9")
    return sorted(pair) == sorted(_digits(draw2, 2))


def group3_hit(multiset_digits: tuple[int, int, int], draw3: str) -> bool:
    if any(x < 0 or x > 9 for x in multiset_digits):
        raise ValueError("digits must be 0..9")
    counts = sorted(multiset_digits)
    if len(set(counts)) != 2:
        raise ValueError("group3 requires exactly one repeated digit")
    return sorted(_digits(draw3, 3)) == counts


def group6_hit(digits3: tuple[int, int, int], draw3: str) -> bool:
    if len(set(digits3)) != 3 or any(x < 0 or x > 9 for x in digits3):
        raise ValueError("group6 requires three distinct digits 0..9")
    return sorted(_digits(draw3, 3)) == sorted(digits3)


def located_1d_hit(position: int, digit: int, draw5: str) -> bool:
    """0=万, 1=千, 2=百, 3=十, 4=个."""
    draw = _digits(draw5, 5)
    if position not in range(5) or digit not in range(10):
        raise ValueError("invalid position or digit")
    return draw[position] == digit


def digit_size(digit: int) -> str:
    if digit not in range(10):
        raise ValueError("digit must be 0..9")
    return "小" if digit <= 4 else "大"


def digit_parity(digit: int) -> str:
    if digit not in range(10):
        raise ValueError("digit must be 0..9")
    return "双" if digit % 2 == 0 else "单"


def last2_property_hit(tens_property: str, units_property: str, draw5: str, mode: str) -> bool:
    draw = _digits(draw5, 5)
    tens, units = draw[3], draw[4]
    if mode == "大小":
        allowed = {"大", "小"}
        fn = digit_size
    elif mode == "单双":
        allowed = {"单", "双"}
        fn = digit_parity
    else:
        raise ValueError("mode must be 大小 or 单双")
    if tens_property not in allowed or units_property not in allowed:
        raise ValueError("invalid property")
    return fn(tens) == tens_property and fn(units) == units_property
