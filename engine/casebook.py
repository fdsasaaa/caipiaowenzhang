from __future__ import annotations

from .analysis_metrics import (
    WINDOW_INDEXES, POSITION_INDEX, current_omission, digit_sum,
    frequency, snapshot, span,
)


def _validate_draws(draws: list[str]) -> None:
    if not draws:
        raise ValueError("draws must not be empty")
    # snapshot validates format and keeps one validation path.
    for draw in draws:
        snapshot(draw, "五星")


def descriptive_case(draws: list[str], selector: str, lookback: int | None = None) -> dict:
    """Build a reproducible descriptive case from chronological draw strings.

    No predictive conclusion is produced. The caller may use the returned metrics
    to explain a technique, but any threshold or claim of predictive value must
    be supplied and separately validated.
    """
    _validate_draws(draws)
    if lookback is not None:
        if lookback <= 0:
            raise ValueError("lookback must be positive")
        sample = draws[-lookback:]
    else:
        sample = draws
    latest = sample[-1]
    snap = snapshot(latest, selector)
    result = {
        "selector": selector,
        "sample_size": len(sample),
        "latest_draw": latest,
        "latest": {
            "values": list(snap.values),
            "sum": snap.sum_value,
            "span": snap.span_value,
            "parity": snap.parity,
            "size": snap.size,
            "distinct": snap.distinct,
            "repeat": snap.repeat,
            "has_neighbor": snap.has_neighbor,
        },
        "sum_series": [digit_sum(d, selector) for d in sample],
        "span_series": [span(d, selector) for d in sample],
        "frequency": frequency(sample, selector),
        "claim_scope": "descriptive_only",
        "predictive_guarantee": False,
    }
    if selector in POSITION_INDEX:
        result["current_omission"] = current_omission(sample, selector)
    return result


def omission_case(draws: list[str], position: str, threshold: int, lookback: int | None = None) -> dict:
    if position not in POSITION_INDEX:
        raise KeyError(position)
    if threshold < 0:
        raise ValueError("threshold must be >= 0")
    base = descriptive_case(draws, position, lookback)
    omissions = base["current_omission"]
    base["threshold"] = threshold
    base["candidates_meeting_threshold"] = [d for d, gap in omissions.items() if gap >= threshold]
    base["method_note"] = "阈值筛选只描述样本状态，不意味着高遗漏数字下一期更可能出现。"
    return base


def frequency_case(draws: list[str], selector: str, lookback: int, hot_top_n: int | None = None) -> dict:
    base = descriptive_case(draws, selector, lookback)
    if hot_top_n is not None:
        if not 1 <= hot_top_n <= 10:
            raise ValueError("hot_top_n must be 1..10")
        ordered = sorted(base["frequency"].items(), key=lambda kv: (-kv[1], kv[0]))
        base["top_frequency_digits"] = [digit for digit, _ in ordered[:hot_top_n]]
        base["method_note"] = "top_frequency_digits只是按样本频次排序，不代表未来命中率提高。"
    return base
