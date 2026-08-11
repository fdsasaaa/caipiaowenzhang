from __future__ import annotations

import re
from dataclasses import dataclass, field

HARD_CLAIM_PATTERNS = (
    re.compile(r"\d{1,3}(?:\.\d+)?\s*%"),
    re.compile(r"\d+\s*注"),
    re.compile(r"命中率|准确率|成功率|胜率"),
    re.compile(r"赔率|返点|奖金|返奖|收益率|利润|盈利"),
    re.compile(r"下一期会|下期会|一定会出|肯定会出"),
)
QUALIFIERS = ("来源提到", "来源声称", "原文提到", "原文声称", "未验证", "资料中提到", "资料声称")


@dataclass
class ClaimEvidenceReport:
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _plain(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html or "")
    return re.sub(r"\s+", " ", text).strip()


def _sentences(text: str) -> list[str]:
    return [x.strip() for x in re.split(r"[。！？!?]+", text) if x.strip()]


def _hard_sentences(content: str) -> list[str]:
    out = []
    for sentence in _sentences(_plain(content)):
        if any(pattern.search(sentence) for pattern in HARD_CLAIM_PATTERNS):
            out.append(sentence)
    return out


def _evidence_covers_sentence(sentence: str, entries: list[dict]) -> bool:
    compact = re.sub(r"\s+", "", sentence)
    for entry in entries:
        claim = re.sub(r"\s+", "", str(entry.get("claim_text") or ""))
        if not claim:
            continue
        # Claim text can be a concise restatement; require a meaningful overlap.
        if claim in compact or compact in claim:
            return True
        tokens = set(re.findall(r"[\u4e00-\u9fff]{2,}|\d+(?:\.\d+)?%?", claim))
        sentence_tokens = set(re.findall(r"[\u4e00-\u9fff]{2,}|\d+(?:\.\d+)?%?", compact))
        if tokens and len(tokens & sentence_tokens) / len(tokens) >= 0.6:
            return True
    return False


def audit_claim_evidence(packet: dict, article: dict) -> ClaimEvidenceReport:
    # Legacy/manual drafts remain valid under their existing review path. V2 auto-drafts opt into this stricter contract.
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
            if claim and not any(q in claim for q in QUALIFIERS):
                errors.append(f"claim_evidence[{index}] unverified source claim must be explicitly qualified")
        elif support_type == "synthetic_case":
            if refs_set != {"case_bundle"}:
                errors.append(f"claim_evidence[{index}] synthetic_case must reference only case_bundle")
            if any(term in claim for term in ("真实开奖", "实盘结果", "历史开奖证明")):
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
