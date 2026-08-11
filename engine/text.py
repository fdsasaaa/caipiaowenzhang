from __future__ import annotations

import hashlib
import re
from collections import Counter

CJK = re.compile(r"[\u4e00-\u9fffA-Za-z0-9]+")


def normalize_text(text: str) -> str:
    parts = CJK.findall((text or "").lower())
    return "".join(parts)


def sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def char_ngrams(text: str, n: int = 3) -> set[str]:
    s = normalize_text(text)
    if len(s) <= n:
        return {s} if s else set()
    return {s[i : i + n] for i in range(len(s) - n + 1)}


def jaccard(a: str, b: str, n: int = 3) -> float:
    sa, sb = char_ngrams(a, n), char_ngrams(b, n)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def fingerprint(*parts: str) -> str:
    canonical = "|".join(normalize_text(p) for p in parts if p)
    return sha256_text(canonical)


def top_terms(text: str, limit: int = 20) -> list[str]:
    tokens = re.findall(r"[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}|\d+", text or "")
    return [x for x, _ in Counter(tokens).most_common(limit)]
