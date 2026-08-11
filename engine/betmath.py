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


def group3_pool(n_digits: int) -> int:
    """Group-3 multisets from n distinct digits: choose pair digit then singleton."""
    n_digits = _positive_int(n_digits, "n_digits")
    return n_digits * max(0, n_digits - 1)


def group6_pool(n_digits: int) -> int:
    """Group-6 unordered triples from n distinct candidate digits."""
    return choose(n_digits, 3)


def located_1d_pool(n_digits: int) -> int:
    """One fixed position with n selected digits."""
    return _positive_int(n_digits, "n_digits")


def theoretical_direct_probability(k_positions: int) -> float:
    k_positions = _positive_int(k_positions, "k_positions")
    if k_positions == 0:
        raise ValueError("k_positions must be >= 1")
    return 1 / (10 ** k_positions)
