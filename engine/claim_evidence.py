from __future__ import annotations

import re
from dataclasses import dataclass, field

from .text import jaccard

_CN_NUMBER = r"[零〇一二三四五六七八九十百千万两点]+"
_CN_BET_COUNT = r"[二三四五六七八九十百千万两]+"
HARD_CLAIM_PATTERNS = (
    re.compile(r"\d{1,3}(?:\.\d+)?\s*%"),
    re.compile(rf"百分之(?:\d+(?:\.\d+)?|{_CN_NUMBER})"),
    re.compile(rf"(?:\d+|{_CN_BET_COUNT})\s*注"),
    re.compile(r"命中率|准确率|成功率|胜率"),
    re.compile(r"赔率|返点|奖金|返奖|收益率|利润|盈利"),
    re.compile(r"下一期会|下期会|一定会出|肯定会出"),
)
_BLOCK_TAG = re.compile(r"</?(?:p|h[1-6]|li|ul|ol|div|section|article|br)\b[^>]*>", re.IGNORECASE)
_ECONOMICS_DISCLAIMERS = (
    "不讨论", "不涉及", "不提供", "不说明", "不引用", "不使用",
    "未核验的", "未经核验的", "没有核验", "尚未核验",
)
_PERFORMANCE_NEGATIONS = (
    "不是命中率", "不是成功率", "不是准确率", "不是胜率",
    "不代表命中率", "不代表任何命中率", "不代表成功率", "不代表准确率", "不代表胜率",
    "不表示更容易中奖", "不代表更容易中奖", "不是优势判断", "不代表预测优势", "不表示预测优势",
    "不是在证明它更准", "不代表下一期会", "不表示下一期会", "不能直接当成未来预测",
    "不能当成未来预测", "不构成未来保证", "不构成未来判断", "不代表未来",
    "不用于证明固定收益", "不用于证明固定胜率", "不用于证明收益", "不用于证明胜率",
    "不负责把", "不负责将",
)
_NEGATION_PREFIX = (
    r"(?:不是|不代表|不表示|不在说|不能说明|不能证明|不用于证明|不用于说明|"
    r"不用于推断|不用于保证|不等于|并不意味着|不意味着|"
    r"不要把|别把|不能把|不应把|不该把|不要将|不能将|不应将|"
    r"不负责把|不负责将|不能被|不应被|不要被)"
)
_NEGATED_PERFORMANCE_RE = re.compile(
    _NEGATION_PREFIX
    + r".{0,24}(?:命中率|准确率|成功率|胜率|固定胜率|收益|收益率|利润|盈利|"
    + r"更容易中奖|预测优势|优势判断|更准)"
)
_POSITIVE_PERFORMANCE_RE = re.compile(
    r"(?:命中率|准确率|成功率|胜率).{0,8}(?:更高|较高|提高|提升|增加|上升|高于|优于|达到)"
    r"|(?:收益率|利润|盈利).{0,8}(?:更高|较高|提高|提升|增加|上升|高于|优于|达到|稳定)"
)
_NEGATED_POSITIVE_PERFORMANCE_RE = re.compile(
    _NEGATION_PREFIX
    + r".{0,24}(?:命中率|准确率|成功率|胜率|收益率|利润|盈利)"
    + r".{0,8}(?:更高|较高|提高|提升|增加|上升|高于|优于|达到|稳定)"
)
_POSITIVE_CLAUSE_PIVOTS = ("但是", "但", "不过", "然而", "实际", "事实上", "同时")
_SYNTHETIC_NEGATIONS = (
    "不是真实开奖", "不是真实开奖记录", "并非真实开奖", "非真实开奖",
    "不是实盘结果", "并非实盘结果", "不是历史开奖", "演示数据",
)
_QUANTITY_RE = re.compile(r"(\d+(?:\.\d+)?)(注|个|期|条|元|倍|%|％)?")


@dataclass
class ClaimEvidenceReport:
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _plain(html: str) -> str:
    text = _BLOCK_TAG.sub("。", html or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"。+", "。", text)
    return re.sub(r"\s+", " ", text).strip(" 。")


def _sentences(text: str) -> list[str]:
    return [x.strip() for x in re.split(r"[。！？!?]+", text) if x.strip()]


def _pure_economics_disclaimer(sentence: str) -> bool:
    if not any(marker in sentence for marker in _ECONOMICS_DISCLAIMERS):
        return False
    return not bool(re.search(r"\d|%|百分之|\b倍\b|元|每注|单注", sentence))


def _has_unnegated_positive_performance(sentence: str) -> bool:
    if not _POSITIVE_PERFORMANCE_RE.search(sentence):
        return False
    negated_positive = bool(_NEGATED_POSITIVE_PERFORMANCE_RE.search(sentence))
    positive_after_pivot = False
    for pivot in _POSITIVE_CLAUSE_PIVOTS:
        if pivot not in sentence:
            continue
        tail = sentence.split(pivot, 1)[1]
        if _POSITIVE_PERFORMANCE_RE.search(tail):
            positive_after_pivot = True
            break
    return (not negated_positive) or positive_after_pivot


def _pure_performance_or_prediction_disclaimer(sentence: str) -> bool:
    """Recognize negative safety language without hiding actual rate claims."""
    if not any(marker in sentence for marker in _PERFORMANCE_NEGATIONS) and not _NEGATED_PERFORMANCE_RE.search(sentence):
        return False
    if re.search(r"\d+(?:\.\d+)?\s*[%％]|百分之", sentence):
        return False
    if re.search(r"(?:命中率|准确率|成功率|胜率)\s*(?:为|是|达到|约|大约)\s*\d", sentence):
        return False
    if _has_unnegated_positive_performance(sentence):
        return False
    if any(marker in sentence for marker in ("下一期会出", "下期会出", "一定会出", "肯定会出")):
        return False
    return True


def _hard_sentences(content: str) -> list[str]:
    out = []
    for sentence in _sentences(_plain(content)):
        if not any(pattern.search(sentence) for pattern in HARD_CLAIM_PATTERNS):
            continue
        if _pure_economics_disclaimer(sentence):
            continue
        if _pure_performance_or_prediction_disclaimer(sentence):
            continue
        out.append(sentence)
    return out


def _compact(value: str) -> str:
    return re.sub(r"\s+", "", value or "")


def _claim_matches(sentence: str, claim: str) -> bool:
    compact = _compact(sentence)
    claim_compact = _compact(claim)
    if not claim_compact:
        return False
    if claim_compact in compact or compact in claim_compact:
        return True
    if jaccard(claim_compact, compact, n=2) >= 0.48:
        return True
    tokens = set(re.findall(r"[\u4e00-\u9fff]{2,}|\d+(?:\.\d+)?%?", claim_compact))
    sentence_tokens = set(re.findall(r"[\u4e00-\u9fff]{2,}|\d+(?:\.\d+)?%?", compact))
    return bool(tokens) and len(tokens & sentence_tokens) / len(tokens) >= 0.6


def _numeric_signature(value: str) -> set[str]:
    compact = _compact(value)
    return set(re.findall(r"\d+(?:\.\d+)?%?", compact))


def _quantity_signature(value: str) -> set[tuple[str, str]]:
    """Return only unit-bearing quantitative facts such as ('45','注').

    Bare parameter digits (e.g. the 0/2/5/7/9 in a candidate pool) are not a
    quantitative hard-claim signature. Keeping them out prevents exact filter
    parameters from poisoning evidence matching for the real hard facts in the
    same sentence: 10注、35注、6注, etc.
    """
    compact = _compact(value).replace("％", "%")
    return {
        (number, unit)
        for number, unit in _QUANTITY_RE.findall(compact)
        if unit
    }


def _evidence_covers_sentence(sentence: str, entries: list[dict]) -> bool:
    factual_entries = [
        entry for entry in entries
        if str(entry.get("support_type") or "") != "editorial"
    ]
    for entry in factual_entries:
        if _claim_matches(sentence, str(entry.get("claim_text") or "")):
            return True

    sentence_quantities = _quantity_signature(sentence)
    if sentence_quantities:
        supported_quantities: set[tuple[str, str]] = set()
        for entry in factual_entries:
            supported_quantities.update(_quantity_signature(str(entry.get("claim_text") or "")))
        if sentence_quantities.issubset(supported_quantities):
            return True

    sentence_numbers = _numeric_signature(sentence)
    if not sentence_numbers:
        return False
    editorial_match = any(
        str(entry.get("support_type") or "") == "editorial"
        and _claim_matches(sentence, str(entry.get("claim_text") or ""))
        for entry in entries
    )
    if not editorial_match:
        return False
    factual_numeric_support = any(
        sentence_numbers.issubset(_numeric_signature(str(entry.get("claim_text") or "")))
        for entry in factual_entries
    )
    return factual_numeric_support


def _presents_synthetic_as_real(claim: str) -> bool:
    if any(marker in claim for marker in _SYNTHETIC_NEGATIONS):
        return False
    return any(term in claim for term in ("真实开奖", "实盘结果", "历史开奖证明"))


def _has_unverified_qualifier(claim: str) -> bool:
    compact = re.sub(r"\s+", "", claim)
    source_attributed = bool(re.search(r"(?:来源(?:文章|资料)?|原文|资料中).{0,8}(?:提到|声称|认为|写到)", compact))
    uncertainty = any(term in compact for term in (
        "未验证", "未独立验证", "未经验证", "尚未验证", "尚未核验", "未经核验",
        "研究假设", "不能升级成事实", "不能视为事实",
    ))
    return source_attributed or uncertainty


def audit_claim_evidence(packet: dict, article: dict) -> ClaimEvidenceReport:
    if article.get("generation_contract_version") != "2.0":
        return ClaimEvidenceReport(True, warnings=["legacy article: claim-evidence v2 gate not required"])

    entries = article.get("claim_evidence")
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(entries, list):
        return ClaimEvidenceReport(False, errors=["claim_evidence must be a list for generation_contract_version=2.0"])

    facts = packet.get("immutable_facts", {})
    allowed_rules = set(facts.get("rule_refs", []) or [])
    allowed_sources = set(facts.get("source_refs", []) or [])
    allowed_refs = allowed_rules | allowed_sources | {"case_bundle"}
    economics_allowed = facts.get("case_scope") == "economics"

    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"claim_evidence[{index}] must be an object")
            continue
        claim = str(entry.get("claim_text") or "").strip()
        claim_type = str(entry.get("claim_type") or "")
        support_type = str(entry.get("support_type") or "")
        refs = entry.get("support_refs") or []
        if not claim:
            errors.append(f"claim_evidence[{index}] missing claim_text")
        if not isinstance(refs, list):
            errors.append(f"claim_evidence[{index}] support_refs must be a list")
            continue
        refs_set = {str(x) for x in refs}
        if support_type == "verified_rule":
            if not refs_set:
                errors.append(f"claim_evidence[{index}] verified_rule requires support_refs")
            if not refs_set.issubset(allowed_rules):
                errors.append(f"claim_evidence[{index}] references rule outside Draft Packet")
        elif support_type == "source_unverified":
            if not refs_set:
                errors.append(f"claim_evidence[{index}] source_unverified requires support_refs")
            if not refs_set.issubset(allowed_sources):
                errors.append(f"claim_evidence[{index}] references source outside Draft Packet")
            if claim and not _has_unverified_qualifier(claim):
                errors.append(f"claim_evidence[{index}] unverified source claim must be explicitly qualified")
        elif support_type == "synthetic_case":
            if refs_set != {"case_bundle"}:
                errors.append(f"claim_evidence[{index}] synthetic_case must reference only case_bundle")
            if _presents_synthetic_as_real(claim):
                errors.append(f"claim_evidence[{index}] synthetic case cannot be presented as real history")
        elif support_type == "editorial":
            if not refs_set.issubset(allowed_refs):
                errors.append(f"claim_evidence[{index}] editorial claim references unknown support_ref")
            elif refs_set:
                warnings.append(f"claim_evidence[{index}] editorial support_refs are non-evidentiary and should be empty")
        else:
            errors.append(f"claim_evidence[{index}] unknown support_type")

        if claim_type == "economics" and not economics_allowed:
            errors.append(f"claim_evidence[{index}] economics claim blocked without verified economics")
        if claim_type in {"performance", "prediction"} and support_type == "verified_rule":
            errors.append(f"claim_evidence[{index}] gameplay rule cannot prove performance/prediction claim")
        if claim_type == "prediction" and support_type != "source_unverified":
            errors.append(f"claim_evidence[{index}] future prediction is not allowed as a system fact")

    hard_sentences = _hard_sentences(str(article.get("content") or ""))
    for sentence in hard_sentences:
        if not _evidence_covers_sentence(sentence, entries):
            errors.append("hard claim sentence lacks claim_evidence: " + sentence[:140])

    if not entries:
        warnings.append("v2 draft contains no explicit claims; verify that article is purely explanatory")
    return ClaimEvidenceReport(passed=not errors, errors=list(dict.fromkeys(errors)), warnings=list(dict.fromkeys(warnings)))