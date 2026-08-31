from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable

from .store import ROOT

POLICY_PATH = ROOT / "policies" / "TITLE_SEO.json"
TITLE_SEO_CONTRACT_VERSION = "1.0"

TITLE_TOPIC_MATCH = "TITLE_TOPIC_MATCH"
TITLE_DUPLICATION_CHECK = "TITLE_DUPLICATION_CHECK"
TITLE_KEYWORD_DIVERSITY = "TITLE_KEYWORD_DIVERSITY"
TITLE_NUMERIC_CLAIM_VERIFIED = "TITLE_NUMERIC_CLAIM_VERIFIED"
TITLE_SEARCH_INTENT_CHECK = "TITLE_SEARCH_INTENT_CHECK"
TITLE_CLICKABILITY_CHECK = "TITLE_CLICKABILITY_CHECK"

DOMAIN_TERMS = (
    "前二", "后二", "前三", "中三", "后三", "前四", "后四", "五星",
    "万位", "千位", "百位", "十位", "个位", "定位胆",
    "直选", "组选3", "组选6", "组选", "组三", "组六",
    "和值", "跨度", "遗漏", "冷热", "冷号", "热号", "频率", "奇偶", "大小",
    "重号", "重复", "号码池", "候选空间", "注数", "组合", "筛选", "参数",
    "样本", "复盘", "验证", "停止条件", "顺序", "位置", "风险",
)

ATOM_LABELS = {
    "sum_range": "和值",
    "span_range": "跨度",
    "omission_threshold": "遗漏",
    "cold_hot_split": "冷热",
    "frequency_window": "频率",
    "odd_even_filter": "奇偶",
    "big_small_filter": "大小",
    "repeat_filter": "重号",
    "position_filter": "位置",
    "digit_pool": "号码池",
}

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[\s\-—_·•，。；;：:、/\\|（）()【】\[\]《》<>“”‘’'\"!?！？]+")
_NUMERIC_RE = re.compile(r"(?<![A-Za-z0-9])(?P<num>\d+(?:\.\d+)?)(?P<unit>%|％|期|元|注|组|个|层|倍|天|小时|分钟)?")


@dataclass
class GateResult:
    passed: bool
    reasons: list[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)


@dataclass
class TitleSEOReview:
    passed: bool
    contract_version: str
    selected_title: str
    candidates: list[str]
    gates: dict[str, GateResult]

    @property
    def errors(self) -> list[str]:
        rows: list[str] = []
        for name, result in self.gates.items():
            if not result.passed:
                rows.extend(f"[{name}] {reason}" for reason in result.reasons)
        return rows

    def as_dict(self) -> dict:
        return {
            "passed": self.passed,
            "contract_version": self.contract_version,
            "selected_title": self.selected_title,
            "candidates": list(self.candidates),
            "gates": {
                name: {
                    "passed": result.passed,
                    "reasons": list(result.reasons),
                    "details": dict(result.details),
                }
                for name, result in self.gates.items()
            },
        }


def load_title_policy(path: Path | None = None) -> dict:
    data = json.loads((path or POLICY_PATH).read_text(encoding="utf-8"))
    if int(data.get("version") or 0) < 1:
        raise ValueError("invalid TITLE_SEO policy")
    if data.get("contract_version") != TITLE_SEO_CONTRACT_VERSION:
        raise ValueError("TITLE_SEO contract version mismatch")
    return data


def plain_text(value: object) -> str:
    text = html.unescape(_TAG_RE.sub(" ", str(value or "")))
    return _WS_RE.sub(" ", text).strip()


def normalize_title(value: object) -> str:
    return _PUNCT_RE.sub("", str(value or "").lower()).strip()


def _bigrams(value: str) -> set[str]:
    compact = normalize_title(value)
    if len(compact) < 2:
        return {compact} if compact else set()
    return {compact[index:index + 2] for index in range(len(compact) - 1)}


def title_similarity(left: object, right: object) -> float:
    a = normalize_title(left)
    b = normalize_title(right)
    if not a or not b:
        return 0.0
    seq = SequenceMatcher(None, a, b).ratio()
    aa = _bigrams(a)
    bb = _bigrams(b)
    union = aa | bb
    jac = len(aa & bb) / len(union) if union else 0.0
    return max(seq, jac)


def _domain_terms(record: dict) -> list[str]:
    texts = "|".join(
        str(record.get(key) or "")
        for key in ("primary_keyword", "search_intent", "subject_play", "play", "summary")
    )
    values: list[str] = []
    for term in DOMAIN_TERMS:
        if term in texts and term not in values:
            values.append(term)
    for atom in record.get("technique_atoms") or []:
        label = ATOM_LABELS.get(str(atom))
        if label and label not in values:
            values.append(label)
    primary = str(record.get("primary_keyword") or "").strip()
    primary = re.sub(r"^(?:分分彩|时时彩)", "", primary)
    for suffix in load_title_policy().get("generic_suffixes", []):
        if primary.endswith(str(suffix)):
            primary = primary[:-len(str(suffix))]
            break
    primary = primary.strip(" ：:，,。")
    if len(primary) >= 3 and primary not in values:
        values.append(primary)
    return values


def _intent_similarity(title: str, intent: str) -> float:
    aa = _bigrams(title)
    bb = _bigrams(intent)
    if not aa or not bb:
        return 0.0
    return len(aa & bb) / len(aa)


def _evidence_corpus(article: dict, packet: dict | None = None, evidence_source: dict | None = None) -> str:
    rows = [
        plain_text(article.get("content")),
        str(article.get("summary") or ""),
        str(article.get("search_intent") or ""),
        str(article.get("meta_description") or ""),
    ]
    for claim in article.get("claim_evidence") or []:
        if isinstance(claim, dict):
            rows.append(str(claim.get("claim_text") or ""))
            rows.append(str(claim.get("evidence_note") or ""))

    sources = [source for source in (packet, evidence_source) if isinstance(source, dict)]
    for source in sources:
        contract = source.get("article_angle_contract") or {}
        facts = contract.get("required_machine_facts") or {}
        for key in ("starting_space", "final_space", "excluded_space", "stage_count"):
            value = facts.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                rows.extend([str(value), f"{value}个", f"{value}注", f"{value}层"])
        pipeline = (source.get("practicality") or {}).get("filter_pipeline_result") or source.get("filter_pipeline_result") or {}
        for key in ("starting_space", "final_space", "total_excluded", "stage_count"):
            value = pipeline.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                rows.extend([str(value), f"{value}个", f"{value}注", f"{value}层"])
        for stage in pipeline.get("stages") or []:
            if not isinstance(stage, dict):
                continue
            for key in ("before_space", "after_space", "excluded_space"):
                value = stage.get(key)
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    rows.extend([str(value), f"{value}个", f"{value}注"])
    return "\n".join(rows)


def numeric_claims(title: object) -> list[str]:
    claims: list[str] = []
    for match in _NUMERIC_RE.finditer(str(title or "")):
        token = match.group("num") + (match.group("unit") or "")
        if token not in claims:
            claims.append(token)
    return claims


def numeric_claim_support(title: str, article: dict, packet: dict | None = None, evidence_source: dict | None = None) -> tuple[bool, list[str]]:
    corpus = _evidence_corpus(article, packet, evidence_source)
    unsupported = [token for token in numeric_claims(title) if token not in corpus]
    return not unsupported, unsupported


def _candidate_structure(title: str) -> str:
    value = str(title or "")
    if "？" in value or "?" in value:
        if "还是" in value or "先" in value:
            return "question_contrast"
        if "为什么" in value:
            return "question_why"
        if "怎么" in value or "如何" in value:
            return "question_how"
        return "question"
    if re.search(r"\d", value):
        return "numeric"
    if "：" in value or ":" in value:
        if value.startswith("从"):
            return "from_to_colon"
        return "editorial_colon"
    if any(marker in value for marker in ("误区", "风险", "边界", "结论", "复盘", "验证")):
        return "analysis"
    return "plain"


def _comparison_records(root: Path | None = None) -> list[dict]:
    root = root or ROOT
    records: dict[str, dict] = {}
    approved_root = root / "articles" / "approved"
    for path in sorted(approved_root.glob("*.json")) if approved_root.is_dir() else []:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(value, dict) and value.get("article_id"):
            records[str(value["article_id"])] = value
    release_root = root / "articles" / "public_release"
    for path in sorted(release_root.glob("*/*.public-r*.json")) if release_root.is_dir() else []:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(value, dict) and value.get("article_id"):
            records[str(value["article_id"])] = value
    return list(records.values())


def formal_title_records(root: Path | None = None) -> list[dict]:
    return _comparison_records(root)


def _topic_gate(article: dict, packet: dict | None) -> GateResult:
    title = str(article.get("title") or article.get("seo_title") or "").strip()
    context = dict(article)
    if packet:
        context.setdefault("primary_keyword", (packet.get("seo") or {}).get("primary_keyword"))
        context.setdefault("search_intent", (packet.get("seo") or {}).get("search_intent"))
        facts = packet.get("immutable_facts") or {}
        context.setdefault("subject_play", facts.get("subject_play") or facts.get("play"))
        context.setdefault("technique_atoms", facts.get("technique_atoms") or [])
    terms = _domain_terms(context)
    hits = [term for term in terms if term and term in title]
    play = str(context.get("subject_play") or context.get("play") or "").strip()
    play_hit = bool(play and play in title)
    technique_hits = [term for term in hits if term not in {play, "筛选", "参数", "验证", "复盘", "风险"}]
    passed = bool(title) and (play_hit or len(technique_hits) >= 1)
    reasons = [] if passed else ["final title does not retain a concrete play/topic signal from the article"]
    return GateResult(passed, reasons, {"matched_terms": hits[:12], "subject_play": play})


def _duplication_gate(article: dict, comparison_records: Iterable[dict], policy: dict) -> GateResult:
    title = str(article.get("title") or article.get("seo_title") or "").strip()
    article_id = str(article.get("article_id") or "")
    best = {"score": 0.0, "article_id": None, "title": None}
    for row in comparison_records:
        other_id = str(row.get("article_id") or "")
        if article_id and other_id == article_id:
            continue
        other_title = str(row.get("title") or row.get("seo_title") or "").strip()
        if not other_title:
            continue
        score = title_similarity(title, other_title)
        if score > best["score"]:
            best = {"score": score, "article_id": other_id or None, "title": other_title}
    threshold = float(policy["duplicate_similarity_threshold"])
    passed = float(best["score"]) < threshold
    reasons = [] if passed else [f"title similarity {best['score']:.3f} >= {threshold:.2f} against {best['article_id'] or 'existing article'}"]
    return GateResult(passed, reasons, best)


def _keyword_diversity_gate(article: dict, policy: dict) -> GateResult:
    title = str(article.get("title") or article.get("seo_title") or "").strip()
    candidates = [str(value).strip() for value in article.get("title_candidates") or [] if str(value).strip()]
    unique = list(dict.fromkeys(candidates))
    reasons: list[str] = []
    minimum = int(policy["candidate_min"])
    maximum = int(policy["candidate_max"])
    if not (minimum <= len(candidates) <= maximum):
        reasons.append(f"title_candidates must contain {minimum}-{maximum} candidates")
    if len(unique) != len(candidates):
        reasons.append("title_candidates contain duplicates")
    if title not in unique:
        reasons.append("final title must be selected from title_candidates")
    subject = str(article.get("subject_lottery") or "分分彩").strip()
    without_prefix = sum(1 for candidate in unique if not candidate.startswith(subject) and not candidate.startswith("时时彩"))
    required_without = int(policy.get("minimum_candidates_without_lottery_prefix") or 2)
    if without_prefix < required_without:
        reasons.append(f"at least {required_without} candidates must not start with the lottery name")
    structures = {_candidate_structure(candidate) for candidate in unique}
    required_structures = int(policy.get("minimum_distinct_candidate_structures") or 3)
    if len(structures) < required_structures:
        reasons.append(f"candidate set needs at least {required_structures} distinct title structures")
    primary = str(article.get("primary_keyword") or "").strip()
    if primary and (title.startswith(primary + "：") or title.startswith(primary + ":")):
        reasons.append("final title mechanically reuses exact primary_keyword as a prefix")
    for pattern in policy.get("generic_prefix_patterns", []):
        if re.search(str(pattern), title, re.IGNORECASE):
            reasons.append("final title uses a banned generic template prefix")
            break
    return GateResult(
        not reasons,
        reasons,
        {
            "candidate_count": len(candidates),
            "unique_count": len(unique),
            "distinct_structures": sorted(structures),
            "candidates_without_lottery_prefix": without_prefix,
        },
    )


def _numeric_gate(article: dict, packet: dict | None, evidence_source: dict | None) -> GateResult:
    title = str(article.get("title") or article.get("seo_title") or "").strip()
    passed, unsupported = numeric_claim_support(title, article, packet, evidence_source)
    reasons = [] if passed else ["unsupported numeric title claim: " + ", ".join(unsupported)]
    return GateResult(passed, reasons, {"numeric_claims": numeric_claims(title), "unsupported": unsupported})


def _search_intent_gate(article: dict, packet: dict | None) -> GateResult:
    title = str(article.get("title") or article.get("seo_title") or "").strip()
    intent = str(article.get("search_intent") or "").strip()
    if packet and not intent:
        intent = str((packet.get("seo") or {}).get("search_intent") or "")
    terms = [term for term in _domain_terms({**article, "search_intent": intent}) if term in intent]
    hits = [term for term in terms if term in title]
    overlap = _intent_similarity(title, intent)
    passed = bool(intent) and (bool(hits) or overlap >= 0.18)
    reasons = [] if passed else ["title does not express the article search intent strongly enough"]
    return GateResult(passed, reasons, {"intent_term_hits": hits[:12], "bigram_overlap": round(overlap, 4)})


def _clickability_gate(article: dict, policy: dict) -> GateResult:
    title = str(article.get("title") or article.get("seo_title") or "").strip()
    reasons: list[str] = []
    if len(title) < int(policy["title_min_chars"]):
        reasons.append("title is too short to express a concrete reader question")
    if len(title) > int(policy["title_max_chars"]):
        reasons.append("title is too long and reads like keyword stuffing")
    for token in policy.get("forbidden_hype_terms", []):
        if str(token) and str(token) in title:
            reasons.append(f"forbidden hype/guarantee term: {token}")
    if title.count("分分彩") + title.count("时时彩") > 1:
        reasons.append("lottery keyword is repeated in the title")
    if title.count("技巧") > 1:
        reasons.append("技巧 is repeated in the title")
    markers = [str(value) for value in policy.get("clickability_markers_any", [])]
    if not any(marker and marker in title for marker in markers) and not re.search(r"\d", title):
        reasons.append("title lacks a concrete question, contrast, number, risk, boundary, review or conclusion hook")
    return GateResult(not reasons, reasons, {"length": len(title)})


def evaluate_title_seo(
    article: dict,
    *,
    packet: dict | None = None,
    comparison_records: Iterable[dict] | None = None,
    evidence_source: dict | None = None,
    policy: dict | None = None,
) -> TitleSEOReview:
    policy = policy or load_title_policy()
    comparisons = list(comparison_records) if comparison_records is not None else formal_title_records()
    gates = {
        TITLE_TOPIC_MATCH: _topic_gate(article, packet),
        TITLE_DUPLICATION_CHECK: _duplication_gate(article, comparisons, policy),
        TITLE_KEYWORD_DIVERSITY: _keyword_diversity_gate(article, policy),
        TITLE_NUMERIC_CLAIM_VERIFIED: _numeric_gate(article, packet, evidence_source),
        TITLE_SEARCH_INTENT_CHECK: _search_intent_gate(article, packet),
        TITLE_CLICKABILITY_CHECK: _clickability_gate(article, policy),
    }
    critical = [str(value) for value in policy.get("critical_gates", [])]
    passed = all(gates[name].passed for name in critical)
    return TitleSEOReview(
        passed=passed,
        contract_version=TITLE_SEO_CONTRACT_VERSION,
        selected_title=str(article.get("title") or article.get("seo_title") or "").strip(),
        candidates=[str(value).strip() for value in article.get("title_candidates") or [] if str(value).strip()],
        gates=gates,
    )


def validate_title_contract_fields(article: dict) -> list[str]:
    errors: list[str] = []
    if article.get("title_seo_contract_version") != TITLE_SEO_CONTRACT_VERSION:
        errors.append("title_seo_contract_version missing or unsupported")
    candidates = article.get("title_candidates")
    if not isinstance(candidates, list):
        errors.append("title_candidates must be a list")
    if not str(article.get("title_selection_reason") or "").strip():
        errors.append("title_selection_reason is required")
    if article.get("title") != article.get("seo_title"):
        errors.append("title and seo_title must use the same selected final title")
    return errors


def _topic_label(record: dict) -> str:
    primary = str(record.get("primary_keyword") or "").strip()
    primary = re.sub(r"^(?:分分彩|时时彩)", "", primary)
    for suffix in load_title_policy().get("generic_suffixes", []):
        suffix = str(suffix)
        if suffix and primary.endswith(suffix):
            primary = primary[:-len(suffix)]
            break
    primary = primary.strip(" ：:，,。")
    if primary:
        return primary
    play = str(record.get("subject_play") or record.get("play") or "玩法")
    terms = _domain_terms(record)
    metric = next((term for term in terms if term not in play and term not in {"筛选", "参数", "验证", "复盘", "风险"}), "")
    return (play + metric).strip() or "这套筛选思路"


def suggest_title_candidates(record: dict, count: int = 3) -> list[str]:
    topic = _topic_label(record)
    play = str(record.get("subject_play") or record.get("play") or "这一玩法")
    angle = str(record.get("information_gain_type") or "")
    pools = {
        "space_math": [
            f"候选空间为什么会变？{topic}的计算过程一次理清",
            f"先算注数，再谈{topic}：哪些数字只是组合数学",
            f"{topic}怎么算才不混淆？从输入空间到结果边界",
        ],
        "execution_checklist": [
            f"做到哪一步应该停？{topic}的复核清单",
            f"{topic}怎么检查才不漏步骤？先看输入、输出和停止条件",
            f"从规则到复核：{play}这套筛选流程最容易错在哪里",
        ],
        "parameter_boundary": [
            f"哪些参数能提前固定？{topic}的边界先说清",
            f"来源经验和系统参数有什么区别？用{topic}拆开看",
            f"{topic}为什么不能看完结果再改？参数边界与常见误区",
        ],
        "multistage_order": [
            f"先后顺序会改变什么？{topic}的多层筛选这样复核",
            f"为什么不能随意换顺序？从{topic}看连续筛选的输入输出",
            f"{topic}做到最后一层之后，为什么应该停止追加条件？",
        ],
        "sample_provenance": [
            f"演示样本能说明什么？{topic}别被当成预测结论",
            f"{topic}里的样本结果从哪来？先分清计算与预测",
            f"从演示数据到数字池：{topic}有哪些证据边界",
        ],
        "mechanics_case": [
            f"这一步到底怎么算？用{topic}把规则和复算过程讲清",
            f"{topic}为什么容易算错？从玩法规则到完整复核",
            f"先看规则，再看案例：{play}里的{topic}怎样正确理解",
        ],
    }
    values = list(pools.get(angle) or [
        f"{topic}到底在研究什么？先把规则和边界说清",
        f"先看复算过程，再谈{topic}：哪些结论不能直接推出",
        f"{topic}为什么容易被误读？从方法到风险边界",
    ])
    return list(dict.fromkeys(values))[:max(1, min(count, 5))]


def public_release_records(root: Path | None = None) -> list[dict]:
    root = root or ROOT
    release_root = root / "articles" / "public_release"
    latest: dict[str, tuple[int, dict, Path]] = {}
    if not release_root.is_dir():
        return []
    for path in sorted(release_root.glob("*/*.public-r*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(value, dict) or not value.get("article_id"):
            continue
        revision = int(value.get("release_revision") or 0)
        article_id = str(value["article_id"])
        previous = latest.get(article_id)
        if previous is None or revision > previous[0]:
            latest[article_id] = (revision, value, path)
    rows: list[dict] = []
    for article_id in sorted(latest):
        revision, value, path = latest[article_id]
        row = dict(value)
        row["_path"] = str(path.relative_to(root)).replace("\\", "/")
        row["_release_revision"] = revision
        rows.append(row)
    return rows


def _escape_cell(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def audit_public_release_titles(root: Path | None = None) -> dict:
    root = root or ROOT
    records = public_release_records(root)
    policy = load_title_policy(root / "policies" / "TITLE_SEO.json")
    intent_groups: dict[tuple, list[str]] = {}
    for row in records:
        key = (
            str(row.get("subject_play") or row.get("play") or ""),
            tuple(sorted(str(value) for value in row.get("technique_atoms") or [])),
            str(row.get("information_gain_type") or ""),
        )
        intent_groups.setdefault(key, []).append(str(row.get("article_id") or ""))

    audit_rows: list[dict] = []
    prefix_count = 0
    recommend_count = 0
    unsupported_numeric_count = 0
    high_similarity_count = 0
    gate_fail_counts = {name: 0 for name in policy.get("critical_gates", [])}
    for row in records:
        title = str(row.get("title") or row.get("seo_title") or "").strip()
        suggestions = suggest_title_candidates(row, 3)
        audit_article = dict(row)
        audit_article["title_candidates"] = list(dict.fromkeys([title, *suggestions]))[:5]
        audit_article["title_seo_contract_version"] = TITLE_SEO_CONTRACT_VERSION
        audit_article["title_selection_reason"] = "legacy inventory audit only"
        comparisons = [other for other in records if other.get("article_id") != row.get("article_id")]
        review = evaluate_title_seo(
            audit_article,
            comparison_records=comparisons,
            policy=policy,
        )
        issues: list[str] = []
        if title.startswith("分分彩"):
            prefix_count += 1
            issues.append("以“分分彩”开头，批量模板感偏强")
        primary = str(row.get("primary_keyword") or "").strip()
        if primary and (title.startswith(primary + "：") or title.startswith(primary + ":")):
            issues.append("直接把Primary Keyword作为标题前缀")
        dup = review.gates[TITLE_DUPLICATION_CHECK]
        audit_threshold = float(policy.get("audit_similarity_threshold") or 0.78)
        if float(dup.details.get("score") or 0) >= audit_threshold:
            high_similarity_count += 1
            issues.append(
                f"与{dup.details.get('article_id') or '其他文章'}标题相似度{float(dup.details.get('score') or 0):.2f}"
            )
        numeric = review.gates[TITLE_NUMERIC_CLAIM_VERIFIED]
        numeric_state = "无数字"
        if numeric.details.get("numeric_claims"):
            if numeric.passed:
                numeric_state = "有正文/规则/计算依据"
            else:
                numeric_state = "缺乏依据：" + "、".join(numeric.details.get("unsupported") or [])
                unsupported_numeric_count += 1
                issues.append("标题数字缺少正文/规则/计算依据")
        key = (
            str(row.get("subject_play") or row.get("play") or ""),
            tuple(sorted(str(value) for value in row.get("technique_atoms") or [])),
            str(row.get("information_gain_type") or ""),
        )
        same_intent = [value for value in intent_groups.get(key, []) if value != row.get("article_id")]
        if same_intent:
            issues.append(f"同玩法/技术/信息增益角度另有{len(same_intent)}篇，需防搜索意图蚕食")
        for name, result in review.gates.items():
            if not result.passed:
                gate_fail_counts[name] = gate_fail_counts.get(name, 0) + 1
                if name not in {TITLE_DUPLICATION_CHECK, TITLE_KEYWORD_DIVERSITY, TITLE_NUMERIC_CLAIM_VERIFIED}:
                    issues.extend(result.reasons)
        issues = list(dict.fromkeys(issues))
        recommend = bool(issues)
        if recommend:
            recommend_count += 1
        audit_rows.append({
            "original_title": title,
            "article_id": row.get("article_id"),
            "path": row.get("_path"),
            "topic": _topic_label(row),
            "primary_keyword": row.get("primary_keyword"),
            "issues": issues,
            "suggested_title_1": suggestions[0] if len(suggestions) > 0 else "",
            "suggested_title_2": suggestions[1] if len(suggestions) > 1 else "",
            "suggested_title_3": suggestions[2] if len(suggestions) > 2 else "",
            "numeric_evidence": numeric_state,
            "recommend_modify": recommend,
            "max_title_similarity": round(float(dup.details.get("score") or 0), 4),
            "nearest_article_id": dup.details.get("article_id"),
        })

    return {
        "schema_version": 1,
        "audit_scope": "formal website-ready public-r1 latest revisions only",
        "formal_public_release_count": len(records),
        "titles_starting_with_fenfen": prefix_count,
        "titles_recommended_for_revision": recommend_count,
        "titles_with_unsupported_numeric_claims": unsupported_numeric_count,
        "titles_with_high_similarity": high_similarity_count,
        "gate_fail_counts": gate_fail_counts,
        "rows": audit_rows,
        "website_side_effects": False,
        "articles_modified": False,
    }


def render_audit_markdown(report: dict) -> str:
    lines = [
        "# 正式 public-r1 文章标题 SEO 审计",
        "",
        f"- 审计范围：{report['audit_scope']}",
        f"- 正式 public-r1：{report['formal_public_release_count']} 篇",
        f"- 以“分分彩”开头：{report['titles_starting_with_fenfen']} 篇",
        f"- 建议进入标题 revision 评估：{report['titles_recommended_for_revision']} 篇",
        f"- 高标题相似度：{report['titles_with_high_similarity']} 篇",
        f"- 标题数字缺少可验证依据：{report['titles_with_unsupported_numeric_claims']} 篇",
        "- 本报告只审计并给候选，不修改 Approved parent、public-r1 正文或网站。",
        "",
        "## Gate 失败统计",
        "",
    ]
    for name, count in report.get("gate_fail_counts", {}).items():
        lines.append(f"- `{name}`: {count}")
    lines.extend([
        "",
        "## 明细",
        "",
        "| 原标题 | 文章ID/文件 | 文章主题 | 主要关键词 | 标题问题 | 建议新标题1 | 建议新标题2 | 建议新标题3 | 数字是否有正文依据 | 是否建议修改 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ])
    for row in report.get("rows", []):
        article_file = f"{row.get('article_id')}<br>{row.get('path')}"
        issues = "；".join(row.get("issues") or []) or "未发现关键问题"
        cells = [
            row.get("original_title"), article_file, row.get("topic"), row.get("primary_keyword"), issues,
            row.get("suggested_title_1"), row.get("suggested_title_2"), row.get("suggested_title_3"),
            row.get("numeric_evidence"), "是" if row.get("recommend_modify") else "否",
        ]
        lines.append("| " + " | ".join(_escape_cell(value) for value in cells) + " |")
    lines.append("")
    return "\n".join(lines)


def write_title_audit(
    *,
    root: Path | None = None,
    json_path: Path | None = None,
    markdown_path: Path | None = None,
) -> dict:
    root = root or ROOT
    report = audit_public_release_titles(root)
    json_path = json_path or (root / "agent" / "results" / "TITLE_SEO_AUDIT_2026-08-24.json")
    markdown_path = markdown_path or (root / "agent" / "results" / "TITLE_SEO_AUDIT_2026-08-24.md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_audit_markdown(report), encoding="utf-8")
    return report
