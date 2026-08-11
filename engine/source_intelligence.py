from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = ROOT / "knowledge" / "TECHNIQUE_TAXONOMY.json"

REPLY_PATTERNS = (
    r"^(?:顶|顶一下|支持|感谢分享|谢谢楼主|好帖|好东西|学习了|路过|看看|沙发)[！!。,.， ]*$",
    r"^(?:顶你一下|支持楼主|感谢楼主|谢谢分享|好贴要顶|看看吧|学习学习|不错不错).{0,24}$",
)
GENERIC_TITLE_TERMS = ("论坛 -", "彩票论坛", "彩票娱乐信息分享领导者")
AD_TERMS = ("加微信", "联系QQ", "开户注册", "注册链接", "代理咨询", "客服QQ", "微信号")
GUARANTEE_TERMS = ("稳赚", "必中", "包赢", "必赚", "百分百中奖", "100%中奖", "稳赢", "无风险", "必出")
MONEY_TERMS = ("盈利", "利润", "收益率", "赚钱", "本金", "提款", "收入", "回本")
PREDICTIVE_TERMS = ("下期会", "下一期会", "下期必", "下一期必", "肯定会出", "一定会出")


def _taxonomy() -> dict:
    return json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))


def _text(row: dict) -> str:
    for key in ("cleaned_content", "content_text", "content", "body", "text"):
        value = row.get(key)
        if value:
            return str(value).strip()
    return ""


def _source_id(row: dict, content: str) -> str:
    existing = str(row.get("source_id") or "").strip()
    if existing:
        return existing
    namespace = str(row.get("source_name") or row.get("source") or "source").strip().upper()
    native = str(row.get("thread_id") or row.get("id") or row.get("url") or "").strip()
    basis = f"{namespace}|{native}|{hashlib.sha256(content.encode('utf-8')).hexdigest()}"
    return "SRC-" + hashlib.sha1(basis.encode("utf-8")).hexdigest()[:20]


def _normal(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _sentence_spans(text: str) -> Iterable[tuple[int, int, str]]:
    start = 0
    for m in re.finditer(r"[。！？!?\n]+", text):
        end = m.end()
        sentence = text[start:end].strip()
        if sentence:
            yield start, end, sentence
        start = end
    tail = text[start:].strip()
    if tail:
        yield start, len(text), tail


def _infer_terms(text: str, mapping: dict[str, list[str]]) -> list[str]:
    low = text.lower()
    return sorted(name for name, terms in mapping.items() if any(str(term).lower() in low for term in terms))


def _atoms(text: str, taxonomy: dict) -> list[str]:
    found: list[str] = []
    for name, patterns in taxonomy.get("canonical_atoms", {}).items():
        if any(re.search(pattern, text, re.I) for pattern in patterns):
            found.append(name)
    return sorted(set(found))


def _positions(text: str, taxonomy: dict) -> list[str]:
    return [p for p in taxonomy.get("positions", []) if p in text]


def _topic_tags(text: str, taxonomy: dict) -> list[str]:
    found = []
    for category, terms in taxonomy.get("categories", {}).items():
        if any(term in text for term in terms):
            found.append(category)
    return sorted(set(found))


def _case_features(text: str) -> dict:
    windows: list[int] = []
    for pattern in (r"近\s*(\d{1,5})\s*期", r"统计\s*(\d{1,5})\s*期", r"前\s*(\d{1,5})\s*期"):
        for match in re.finditer(pattern, text):
            value = int(match.group(1))
            if 1 <= value <= 100000 and value not in windows:
                windows.append(value)
    numbers: list[str] = []
    for pattern in (r"(?<!\d)\d{3,5}(?!\d)", r"(?<!\d)[0-9](?:[,、 ]+[0-9]){2,8}(?!\d)"):
        for match in re.finditer(pattern, text):
            value = _normal(match.group(0))
            if value not in numbers:
                numbers.append(value)
            if len(numbers) >= 8:
                break
    return {
        "has_explicit_example": bool(re.search(r"例如|比如|举例|以.{0,20}为例", text)),
        "uses_previous_draw": bool(re.search(r"上期|上一期|当期开奖号|上期开奖", text)),
        "targets_next_draw": bool(re.search(r"下期|下一期|本期", text)),
        "history_windows": windows[:8],
        "case_number_samples": numbers[:8],
    }


def _claim_type(sentence: str) -> tuple[str, int] | None:
    if any(term in sentence for term in GUARANTEE_TERMS):
        return "guaranteed_outcome", 100
    if re.search(r"(?<!\d)\d{1,3}(?:\.\d+)?\s*%", sentence):
        return "percentage_performance", 90
    if any(term in sentence for term in MONEY_TERMS):
        return "money_or_profit", 85
    if any(term in sentence for term in PREDICTIVE_TERMS):
        return "future_prediction", 90
    if re.search(r"(?:命中率|准确率|成功率|胜率)", sentence):
        return "performance_claim", 85
    return None


def extract_claims(text: str, source_id: str) -> list[dict]:
    claims: list[dict] = []
    for start, end, sentence in _sentence_spans(text):
        typed = _claim_type(sentence)
        if not typed:
            continue
        claim_type, risk = typed
        snippet = _normal(sentence)[:220]
        claim_id = "CLM-" + hashlib.sha1(f"{source_id}|{start}|{snippet}".encode("utf-8")).hexdigest()[:18]
        claims.append({
            "claim_id": claim_id,
            "claim_type": claim_type,
            "text": snippet,
            "evidence": {
                "source_id": source_id,
                "char_start": start,
                "char_end": end,
                "snippet": snippet,
                "snippet_sha256": hashlib.sha256(snippet.encode("utf-8")).hexdigest(),
            },
            "verification_status": "unverified_source_claim",
            "risk_score": risk,
        })
        if len(claims) >= 20:
            break
    return claims


def quality_assessment(row: dict, content: str) -> dict:
    title = str(row.get("title") or "").strip()
    stripped = _normal(content)
    signals: list[str] = []
    score = 100
    if not stripped:
        return {"score": 0, "decision": "reject", "signals": ["empty_body"]}
    if len(stripped) < 40:
        score -= 55; signals.append("very_short_body")
    elif len(stripped) < 100:
        score -= 25; signals.append("short_body")
    if any(term in title for term in GENERIC_TITLE_TERMS):
        score -= 55; signals.append("generic_or_printable_title")
    if any(re.match(pattern, stripped, re.I) for pattern in REPLY_PATTERNS):
        score -= 80; signals.append("reply_boilerplate")
    if any(term in stripped for term in AD_TERMS):
        score -= 45; signals.append("advertising_or_contact_content")
    title_norm = _normal(title)
    if title_norm and stripped in {title_norm, _normal(str(row.get("author") or "") + " " + title_norm)}:
        score -= 60; signals.append("body_looks_like_header_only")
    score = max(0, min(100, score))
    decision = "keep" if score >= 65 else ("quarantine" if score >= 35 else "reject")
    return {"score": score, "decision": decision, "signals": signals}


def build_knowledge_card(row: dict, taxonomy: dict | None = None) -> dict:
    taxonomy = taxonomy or _taxonomy()
    content = _text(row)
    source_id = _source_id(row, content)
    title = str(row.get("title") or "").strip()
    keywords = str(row.get("keywords") or "")
    combined = f"{title}\n{keywords}\n{content}"
    quality = quality_assessment(row, content)
    atoms = _atoms(combined, taxonomy)
    claims = extract_claims(content, source_id)
    knowledge_status = "eligible_after_rule_binding"
    if quality["decision"] != "keep":
        knowledge_status = quality["decision"]
    elif not atoms:
        knowledge_status = "idea_only"
    return {
        "schema_version": "2.0",
        "source_id": source_id,
        "source_name": row.get("source_name") or row.get("source") or "unknown",
        "native_id": row.get("thread_id") or row.get("id"),
        "url": row.get("url"),
        "title": title,
        "classification": row.get("classification") or row.get("forum_name") or "",
        "published_at": row.get("published_at"),
        "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "content_length": len(content),
        "quality": quality,
        "lotteries": _infer_terms(combined, taxonomy.get("lottery_terms", {})),
        "positions": _positions(combined, taxonomy),
        "technique_atoms": atoms,
        "topic_tags": _topic_tags(combined, taxonomy),
        "case_features": _case_features(content),
        "claims": claims,
        "claim_risk_max": max((c["risk_score"] for c in claims), default=0),
        "verification_status": "unverified_source",
        "knowledge_status": knowledge_status,
        "requires_rule_binding": True,
        "publishable": False,
    }


def read_source_rows(path: Path) -> Iterable[dict]:
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("articles", payload.get("rows", payload)) if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            raise ValueError("JSON source file must contain a list or articles/rows list")
        yield from rows
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            yield json.loads(line)


def ingest_file(input_path: Path, output_path: Path, quarantine_path: Path | None = None) -> dict:
    taxonomy = _taxonomy()
    cards = [build_knowledge_card(row, taxonomy) for row in read_source_rows(input_path)]
    seen_hashes: dict[str, str] = {}
    kept: list[dict] = []
    quarantined: list[dict] = []
    for card in cards:
        content_hash = card["content_sha256"]
        if content_hash in seen_hashes:
            card["quality"]["signals"].append("exact_content_duplicate")
            card["quality"]["decision"] = "reject"
            card["knowledge_status"] = "reject"
            card["duplicate_of_source_id"] = seen_hashes[content_hash]
        else:
            seen_hashes[content_hash] = card["source_id"]
        (kept if card["knowledge_status"] not in {"reject", "quarantine"} else quarantined).append(card)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n" for c in kept), encoding="utf-8")
    if quarantine_path:
        quarantine_path.parent.mkdir(parents=True, exist_ok=True)
        quarantine_path.write_text("".join(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n" for c in quarantined), encoding="utf-8")
    return {
        "input": len(cards),
        "knowledge_cards": len(kept),
        "quarantined_or_rejected": len(quarantined),
        "with_technique_atoms": sum(bool(c["technique_atoms"]) for c in kept),
        "with_claims": sum(bool(c["claims"]) for c in kept),
        "output": str(output_path),
        "quarantine": str(quarantine_path) if quarantine_path else None,
    }
