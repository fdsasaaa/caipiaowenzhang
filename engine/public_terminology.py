from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

READER_FIELDS = (
    "title",
    "seo_title",
    "meta_description",
    "primary_keyword",
    "secondary_keywords",
    "search_intent",
    "summary",
    "category",
    "tags",
    "content",
)

QUALIFIED_LEGACY_MARKERS = (
    "历史",
    "规则库",
    "规则名",
    "内部",
    "来源原文",
    "原文术语",
    "归档",
    "mechanics",
)

DEFAULT_ARTICLE_GLOBS = (
    "articles/approved/*.json",
    "articles/drafts/*.json",
    "articles/published/*.json",
    "smoke/batch*/articles/*.json",
    "smoke/batch*/approved/*.json",
)


@dataclass
class TerminologyFinding:
    path: str
    article_id: str
    field: str
    message: str
    severity: str = "error"


@dataclass
class TerminologyAudit:
    scanned_files: int = 0
    ffc_articles: int = 0
    findings: list[TerminologyFinding] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(row.severity == "error" for row in self.findings)

    def as_dict(self) -> dict:
        return {
            "passed": self.passed,
            "scanned_files": self.scanned_files,
            "ffc_articles": self.ffc_articles,
            "errors": sum(row.severity == "error" for row in self.findings),
            "warnings": sum(row.severity == "warning" for row in self.findings),
            "findings": [row.__dict__ for row in self.findings],
        }


def _text(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return ""


def is_ffc_reader_article(article: dict) -> bool:
    subject = str(article.get("subject_lottery") or "")
    if subject == "分分彩":
        return True
    visible = " ".join(_text(article.get(field)) for field in READER_FIELDS if field != "content")
    return "分分彩" in visible


def _body_legacy_sentences(content: str) -> list[str]:
    plain = re.sub(r"<[^>]+>", "。", content or "")
    return [
        sentence.strip()
        for sentence in re.split(r"[。！？!?]+", plain)
        if "时时彩" in sentence
    ]


def audit_article(path: str, article: dict) -> list[TerminologyFinding]:
    if not is_ffc_reader_article(article):
        return []

    article_id = str(article.get("article_id") or "unknown")
    findings: list[TerminologyFinding] = []
    strict_fields = (
        "title", "seo_title", "meta_description", "primary_keyword",
        "secondary_keywords", "search_intent", "summary", "category", "tags",
    )
    for field in strict_fields:
        value = _text(article.get(field))
        if "时时彩" in value:
            findings.append(TerminologyFinding(
                path=path,
                article_id=article_id,
                field=field,
                message="分分彩 reader-facing field contains legacy 时时彩 terminology",
            ))

    for sentence in _body_legacy_sentences(_text(article.get("content"))):
        if any(marker in sentence for marker in QUALIFIED_LEGACY_MARKERS):
            continue
        findings.append(TerminologyFinding(
            path=path,
            article_id=article_id,
            field="content",
            message="分分彩 body contains unqualified legacy 时时彩 terminology: " + sentence[:120],
        ))
    return findings


def audit_repository(root: Path) -> TerminologyAudit:
    audit = TerminologyAudit()
    paths: set[Path] = set()
    for pattern in DEFAULT_ARTICLE_GLOBS:
        paths.update(root.glob(pattern))

    for path in sorted(paths):
        if not path.is_file():
            continue
        audit.scanned_files += 1
        try:
            article = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            audit.findings.append(TerminologyFinding(
                path=str(path.relative_to(root)),
                article_id="unknown",
                field="file",
                message=f"article JSON cannot be audited: {exc}",
            ))
            continue
        if not isinstance(article, dict):
            audit.findings.append(TerminologyFinding(
                path=str(path.relative_to(root)),
                article_id="unknown",
                field="file",
                message="article JSON must be an object",
            ))
            continue
        if is_ffc_reader_article(article):
            audit.ffc_articles += 1
        audit.findings.extend(audit_article(str(path.relative_to(root)), article))
    return audit
