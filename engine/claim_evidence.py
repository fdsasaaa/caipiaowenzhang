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
_SYNTHETIC_NEGATIONS = (
    "不是真实开奖", "不是真实开奖记录", "并非真实开奖", "非真实开奖",
    "不是实盘结果", "并非实盘结果", "不是历史开奖", "演示数据",
)


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


def _hard_sentences(content: str) -> list[str]:
    out = []
    for sentence in _sentences(_plain(content)):
        if not any(pattern.search(sentence) for pattern in HARD_CLAIM_PATTERNS):
            continue
        if _pure_economics_disclaimer(sentence):
            continue
        out.append(sentence)
    return out


def _evidence_covers_sentence(sentence: str, entries: list[dict]) -> bool:
    compact = re.sub(r"\s+", "", sentence)
    for entry in entries:
        claim = re.sub(r"\s+", "", str(entry.get("claim_text") or ""))
        if not claim:
            continue
        if claim in compact or compact in claim:
            return True
        if jaccard(claim, compact, n=2) >= 0.48:
            return True
        tokens = set(re.findall(r"[\u4e00-\u9fff]{2,}|\d+(?:\.\d+)?%?", claim))
        sentence_tokens = set(re.findall(r"[\u4e00-\u9fff]{2,}|\d+(?:\.\d+)?%?", compact))
        if tokens and len(tokens & sentence_tokens) / len(tokens) >= 0.6:
            return True
    return False


def _presents_synthetic_as_real(claim: str) -> bool:
    if any(marker in claim for marker in _SYNTHETIC_NEGATIONS):
        return False
    return any(term in claim for term in ("真实开奖", "实盘结果", "历史开奖证明"))


def _has_unverified_qualifier(claim: str) -> bool:
    """Accept natural source-attribution variants without weakening the requirement."""
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
            if refs_set:
                errors.append(f"claim_evidence[{index}] editorial claim must not carry support_refs")
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
    return ClaimEvidenceReport(passed=not errors, errors=list(dict.fromkeys(errors)), warnings=warnings)
