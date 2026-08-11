from __future__ import annotations

from math import comb, prod


def _positive_int(value: int, name: str) -> int:
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def direct_product(*position_counts: int) -> int:
    """Number of ordered direct bets from independent per-position selections."""
    if not position_counts:
        return 0
    counts = [_positive_int(x, "position_count") for x in position_counts]
    return prod(counts)


def choose(n: int, k: int) -> int:
    n = _positive_int(n, "n")
    k = _positive_int(k, "k")
    if k > n:
        return 0
    return comb(n, k)


def group2_pool(n_digits: int) -> int:
    """Two-star unordered pairs from n distinct candidate digits."""
    return choose(n_digits, 2)


def group2_banker_single(banker_count: int = 1, digit_domain: int = 10) -> int:
    """Two-star group bets containing at least one of the banker digits; exact for one banker."""
    banker_count = _positive_int(banker_count, "banker_count")
    digit_domain = _positive_int(digit_domain, "digit_domain")
    if banker_count == 0 or banker_count > digit_domain:
        return 0
    return choose(digit_domain, 2) - choose(digit_domain - banker_count, 2)


def group3_pool(n_digits: int) -> int:
    """Group-3 multisets from n distinct digits: choose pair digit then singleton."""
    n_digits = _positive_int(n_digits, "n_digits")
    return n_digits * max(0, n_digits - 1)


def group6_pool(n_digits: int) -> int:
    """Group-6 unordered triples from n distinct candidate digits."""
    return choose(n_digits, 3)


def group3_group6_banker_single(digit_domain: int = 10) -> int:
    """Three-star mixed group patterns containing one fixed banker digit: 18 group3 + C(9,2) group6 = 54 for domain 10."""
    digit_domain = _positive_int(digit_domain, "digit_domain")
    if digit_domain < 2:
        return 0
    group3 = 2 * (digit_domain - 1)
    group6 = choose(digit_domain - 1, 2)
    return group3 + group6


def group4_pool(n_digits: int) -> int:
    """Four-digit AAAB pattern count."""
    n_digits = _positive_int(n_digits, "n_digits")
    return n_digits * max(0, n_digits - 1)


def group6_four_pool(n_digits: int) -> int:
    """Four-digit AABB pattern count."""
    return choose(n_digits, 2)


def group12_pool(n_digits: int) -> int:
    """Four-digit AABC pattern count."""
    n_digits = _positive_int(n_digits, "n_digits")
    return n_digits * choose(max(0, n_digits - 1), 2)


def group24_pool(n_digits: int) -> int:
    """Four-digit ABCD pattern count."""
    return choose(n_digits, 4)


def group60_five_pool(n_digits: int) -> int:
    """Five-digit AABCD pattern classes; platform semantics still require mapping."""
    n_digits = _positive_int(n_digits, "n_digits")
    return n_digits * choose(max(0, n_digits - 1), 3)


def group120_five_pool(n_digits: int) -> int:
    """Five-digit ABCDE all-distinct pattern classes; platform semantics still require mapping."""
    return choose(n_digits, 5)


def located_1d_pool(n_digits: int) -> int:
    """One fixed position with n selected digits."""
    return _positive_int(n_digits, "n_digits")


def theoretical_direct_probability(k_positions: int) -> float:
    k_positions = _positive_int(k_positions, "k_positions")
    if k_positions == 0:
        raise ValueError("k_positions must be >= 1")
    return 1 / (10 ** k_positions)
