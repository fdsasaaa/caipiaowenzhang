from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8", newline="\n")


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"patch anchor not found in {path}: {old[:100]!r}")
    write(path, text.replace(old, new, 1))


def append_once(path: str, marker: str, addition: str) -> None:
    text = read(path)
    if marker in text:
        return
    write(path, text.rstrip() + "\n\n" + addition.strip() + "\n")


def patch_title_runtime() -> None:
    addition = r'''
# --- Title SEO V1.0 runtime selection layer ---
def _body_focus(record: dict) -> str:
    content = plain_text(record.get("content"))
    for marker in (
        "停止条件", "常见误区", "候选空间", "参数预注册", "样本外验证", "组合数学",
        "风险边界", "输入输出", "复算", "注数", "遗漏", "冷热", "和值", "跨度",
    ):
        if marker in content:
            return marker
    return "规则边界"


def suggest_title_candidates(record: dict, count: int = 5) -> list[str]:
    """Generate diverse, evidence-safe candidates after body generation.

    This intentionally uses the completed article (content/summary/search intent) plus
    immutable topic metadata.  It never invents a numeric hook; numeric candidates are
    only accepted later when TITLE_NUMERIC_CLAIM_VERIFIED can trace them to evidence.
    """
    topic = _topic_label(record)
    play = str(record.get("subject_play") or record.get("play") or "这一玩法").strip()
    angle = str(record.get("information_gain_type") or "")
    focus = _body_focus(record)
    pools = {
        "space_math": [
            f"候选空间为什么会变？{topic}的计算过程一次理清",
            f"先算注数，再谈{topic}：组合数学能说明到哪一步",
            f"从输入到结果：{topic}的空间计算与{focus}",
            f"{topic}怎么算才不混淆？复核候选空间的三个关键点",
            f"看懂{play}的{topic}，先分清计算结果和预测结论",
        ],
        "execution_checklist": [
            f"做到哪一步应该停？{topic}的复核清单",
            f"{topic}怎么检查才不漏步骤？先看输入、输出和停止条件",
            f"从规则到复核：{play}这套筛选流程最容易错在哪里",
            f"先固定步骤，再看结果：{topic}的执行边界",
            f"{topic}不是越筛越好，关键在什么时候停止",
        ],
        "parameter_boundary": [
            f"哪些参数能提前固定？{topic}的边界先说清",
            f"来源经验和系统参数有什么区别？用{topic}拆开看",
            f"从参数到结果：{topic}哪些能预设，哪些不能事后改",
            f"{topic}为什么不能看完结果再调？常见误区与风险边界",
            f"先定规则还是先看样本？{play}参数问题这样区分",
        ],
        "multistage_order": [
            f"先后顺序为什么重要？{topic}的多层筛选这样复核",
            f"从第一层到最后一层：{topic}的输入输出与停止边界",
            f"{topic}的关键不只是筛选，顺序和停止条件同样重要",
            f"为什么不能随意换顺序？用{topic}看连续筛选逻辑",
            f"做到最后一层之后呢？{topic}为什么不该继续追加条件",
        ],
        "sample_provenance": [
            f"演示样本能说明什么？{topic}别被当成预测结论",
            f"从演示数据到结果：{topic}的证据边界在哪里",
            f"{topic}里的样本结果从哪来？先分清计算与预测",
            f"先看样本怎么生成，再谈{topic}能不能被复现",
            f"{play}的{topic}为什么必须标清演示数据来源",
        ],
        "mechanics_case": [
            f"这一步到底怎么算？用{topic}把规则和复算过程讲清",
            f"从玩法规则到完整案例：{topic}应该怎样复核",
            f"{topic}为什么容易算错？关键在输入、计算和{focus}",
            f"先看规则，再看案例：{play}里的{topic}怎样正确理解",
            f"看懂{topic}不靠口诀，先把计算逻辑拆开",
        ],
    }
    values = list(pools.get(angle) or [
        f"{topic}到底在研究什么？先把规则和边界说清",
        f"从规则到复盘：{topic}应该怎样验证才不越界",
        f"先看复算过程，再谈{topic}：哪些结论不能直接推出",
        f"{topic}为什么容易被误读？从方法到风险边界",
        f"看懂{play}里的{topic}，先分清事实、计算和推断",
    ])
    return list(dict.fromkeys(values))[:max(3, min(int(count or 5), 5))]


def apply_title_seo(
    article: dict,
    *,
    packet: dict | None = None,
    comparison_records: Iterable[dict] | None = None,
    evidence_source: dict | None = None,
    policy: dict | None = None,
) -> TitleSEOReview:
    """Generate candidates from completed body, select only a gate-passing final title."""
    policy = policy or load_title_policy()
    context = dict(article)
    if packet:
        seo = packet.get("seo") or {}
        facts = packet.get("immutable_facts") or {}
        contract = packet.get("article_angle_contract") or {}
        context.setdefault("primary_keyword", seo.get("primary_keyword"))
        context.setdefault("search_intent", seo.get("search_intent"))
        context.setdefault("subject_lottery", facts.get("subject_lottery") or facts.get("lottery"))
        context.setdefault("subject_play", facts.get("subject_play") or facts.get("play"))
        context.setdefault("play", facts.get("play"))
        context.setdefault("technique_atoms", facts.get("technique_atoms") or [])
        context.setdefault("information_gain_type", contract.get("angle_type") or facts.get("information_gain_type"))

    # public-r1 is a new editorial surface and must regenerate candidates from its
    # rewritten body instead of inheriting the Approved parent's candidate set.
    inherited_allowed = evidence_source is None
    raw_candidates = article.get("title_candidates") if inherited_allowed else None
    candidates = [str(value).strip() for value in raw_candidates or [] if str(value).strip()]
    if not (int(policy["candidate_min"]) <= len(candidates) <= int(policy["candidate_max"])):
        candidates = suggest_title_candidates(context, int(policy["candidate_max"]))
    candidates = list(dict.fromkeys(candidates))[: int(policy["candidate_max"])]
    article["title_candidates"] = candidates
    article["title_seo_contract_version"] = TITLE_SEO_CONTRACT_VERSION
    article["title_selection_reason"] = (
        "正文完成后生成候选；按主题匹配、重复度、关键词结构多样性、数字真实性、搜索意图和可读性 Gate 选择。"
    )

    comparisons = list(comparison_records) if comparison_records is not None else formal_title_records()
    selected_review: TitleSEOReview | None = None
    selected_title = candidates[0] if candidates else str(article.get("title") or article.get("seo_title") or "").strip()
    for candidate in candidates:
        probe = dict(article)
        probe["title"] = candidate
        probe["seo_title"] = candidate
        probe["title_candidates"] = candidates
        review = evaluate_title_seo(
            probe,
            packet=packet,
            comparison_records=comparisons,
            evidence_source=evidence_source,
            policy=policy,
        )
        if selected_review is None:
            selected_review = review
        if review.passed:
            selected_title = candidate
            selected_review = review
            break

    article["title"] = selected_title
    article["seo_title"] = selected_title
    final_review = evaluate_title_seo(
        article,
        packet=packet,
        comparison_records=comparisons,
        evidence_source=evidence_source,
        policy=policy,
    )
    article["title_review"] = final_review.as_dict()
    return final_review
'''
    append_once("engine/title_seo.py", "def apply_title_seo(", addition)


def patch_generation_normalization() -> None:
    path = "engine/generation_normalization.py"
    text = read(path)
    if "from .title_seo import apply_title_seo" not in text:
        text = text.replace("import re\n", "import re\n\nfrom .title_seo import apply_title_seo\n", 1)
    marker = "def normalize_generation_metadata(article: dict) -> dict:"
    if marker in text:
        head = text.split(marker, 1)[0]
        replacement = '''def normalize_generation_metadata(article: dict, packet: dict | None = None) -> dict:\n    \"\"\"Narrow deterministic metadata cleanup plus post-body Title SEO V1.0.\n\n    The prose is never rewritten here. Title candidates are generated only after the\n    completed body exists, then the final title is selected by deterministic gates.\n    \"\"\"\n    claims = article.get(\"claim_evidence\")\n    if isinstance(claims, list):\n        for row in claims:\n            if not isinstance(row, dict):\n                continue\n            if row.get(\"claim_type\") != \"editorial\":\n                continue\n            if row.get(\"support_type\") != \"source_unverified\":\n                continue\n            if not _is_pure_editorial_scope_disclaimer(str(row.get(\"claim_text\") or \"\")):\n                continue\n            row[\"support_type\"] = \"editorial\"\n            row[\"support_refs\"] = []\n            row[\"evidence_note\"] = \"编辑范围/风险说明，不是来源事实声明。\"\n\n    apply_title_seo(article, packet=packet)\n    return article\n'''
        text = head + replacement
    elif "def normalize_generation_metadata(article: dict, packet: dict | None = None)" not in text:
        raise RuntimeError("normalization function anchor missing")
    write(path, text)


def patch_production_controller() -> None:
    replace_once(
        "engine/production_controller.py",
        "article = normalize_generation_metadata(generation.article)",
        "article = normalize_generation_metadata(generation.article, packet=packet)",
    )


def patch_ai_prompt() -> None:
    replace_once(
        "engine/ai_generation.py",
        "1. immutable_facts、SEO主词、rule_refs/source_refs、网站分类不可篡改。title 与 seo_title 应自然包含 exact primary_keyword；不要堆砌关键词。\\n",
        "1. immutable_facts、SEO主词、rule_refs/source_refs、网站分类不可篡改。primary_keyword字段必须保持exact值；title/seo_title只是正文阶段的工作标题，不要求逐字包含Primary Keyword，最终标题会在正文完成后由Title SEO编辑层重新生成与验收。\\n",
    )
    replace_once(
        "engine/ai_generation.py",
        "17. 本篇面向读者的彩种显示名统一优先使用‘分分彩’。title、seo_title、meta_description、primary_keyword、summary、tags和普通正文不要用‘时时彩’替代‘分分彩’。\\n",
        "17. 本篇面向读者的彩种显示名统一优先使用‘分分彩’。meta_description、primary_keyword、summary、tags和普通正文不要用‘时时彩’替代‘分分彩’；title/seo_title允许根据真实搜索问题省略彩种名或把彩种名放在中后部，不强制以‘分分彩’开头。\\n",
    )


def patch_approval() -> None:
    path = "engine/approval.py"
    text = read(path)
    if "from .title_seo import evaluate_title_seo" not in text:
        text = text.replace(
            "from .text import sha256_text\n",
            "from .text import sha256_text\nfrom .title_seo import evaluate_title_seo\n",
            1,
        )
    old = "    angle_report = evaluate_article_angle(packet, article)\n    if angle_report.contracted:\n"
    new = "    angle_report = evaluate_article_angle(packet, article)\n    title_report = None\n    if article.get(\"title_seo_contract_version\"):\n        title_report = evaluate_title_seo(article, packet=packet)\n        article[\"title_review\"] = title_report.as_dict()\n    if angle_report.contracted:\n"
    if new not in text:
        if old not in text:
            raise RuntimeError("approval title-report anchor missing")
        text = text.replace(old, new, 1)
    old = "        *editorial_report.errors, *angle_report.errors, *seo_errors,\n"
    new = "        *editorial_report.errors, *angle_report.errors, *(title_report.errors if title_report else []), *seo_errors,\n"
    if new not in text:
        if old not in text:
            raise RuntimeError("approval errors anchor missing")
        text = text.replace(old, new, 1)
    old = "        and angle_report.passed\n    )\n"
    new = "        and angle_report.passed\n        and (title_report is None or title_report.passed)\n    )\n"
    if new not in text:
        if old not in text:
            raise RuntimeError("approval passed anchor missing")
        text = text.replace(old, new, 1)
    title_meta = '''    for field in (\"title_seo_contract_version\", \"title_candidates\", \"title_selection_reason\", \"title_review\"):\n        if article.get(field) is not None:\n            package[field] = article[field]\n'''
    anchor = "    provider_response_id = article.get(\"provider_response_id\") or existing.get(\"provider_response_id\")\n"
    if title_meta not in text:
        if anchor not in text:
            raise RuntimeError("publish title metadata anchor missing")
        text = text.replace(anchor, title_meta + anchor, 1)
    registry_meta = '''    for field in (\"title_seo_contract_version\", \"title_candidates\", \"title_selection_reason\", \"title_review\"):\n        if article.get(field) is not None:\n            changes[field] = article[field]\n'''
    anchor2 = "    angle_contract = packet.get(\"article_angle_contract\") or {}\n"
    # The first angle_contract is in _publish_package; insert after the second occurrence for registry.
    if registry_meta not in text:
        first = text.find(anchor2)
        second = text.find(anchor2, first + len(anchor2)) if first >= 0 else -1
        if second < 0:
            raise RuntimeError("registry title metadata anchor missing")
        text = text[:second] + registry_meta + text[second:]
    write(path, text)


def patch_creator_first() -> None:
    path = "engine/creator_first.py"
    text = read(path)
    if "from .title_seo import apply_title_seo" not in text:
        text = text.replace(
            "from .store import ROOT, iter_registry\n",
            "from .store import ROOT, iter_registry\nfrom .title_seo import apply_title_seo\n",
            1,
        )
    old = "    packet = build_creator_packet(request, manifest, article)\n    approval = evaluate_for_approval(packet, article)\n"
    new = "    packet = build_creator_packet(request, manifest, article)\n    title_review = apply_title_seo(article, packet=packet)\n    article[\"title_review\"] = title_review.as_dict()\n    approval = evaluate_for_approval(packet, article)\n"
    if new not in text:
        if old not in text:
            raise RuntimeError("creator title integration anchor missing")
        text = text.replace(old, new, 1)
    write(path, text)


def patch_formal_inventory() -> None:
    path = "engine/formal_approved_inventory.py"
    text = read(path)
    if "from .title_seo import validate_title_contract_fields" not in text:
        text = text.replace(
            "from .text import sha256_text\n",
            "from .text import sha256_text\nfrom .title_seo import validate_title_contract_fields\n",
            1,
        )
    anchor = "    if content_hash != sha256_text(content):\n        raise FormalInventoryError(\"content_hash does not match content\")\n\n"
    addition = anchor + '''    if package.get(\"title_seo_contract_version\"):\n        title_errors = validate_title_contract_fields(package)\n        review = package.get(\"title_review\") or {}\n        if title_errors:\n            raise FormalInventoryError(\"Title SEO contract invalid: \" + \"; \".join(title_errors))\n        if review.get(\"passed\") is not True:\n            raise FormalInventoryError(\"Title SEO review must pass before formal inventory\")\n\n'''
    if "Title SEO review must pass before formal inventory" not in text:
        if anchor not in text:
            raise RuntimeError("formal inventory title anchor missing")
        text = text.replace(anchor, addition, 1)
    write(path, text)


def patch_public_release() -> None:
    path = "engine/daily_website_ready.py"
    text = read(path)
    if "from .title_seo import apply_title_seo" not in text:
        text = text.replace(
            "from .text import sha256_text\n",
            "from .text import sha256_text\nfrom .title_seo import apply_title_seo\n",
            1,
        )
    text = text.replace(
        "必须保留玩法机制、文章主题和 exact Primary Keyword 的搜索意图，但不要复制具体执行方案。\\n",
        "必须保留玩法机制、文章主题和 Primary Keyword 所代表的搜索意图，但不要为了SEO把 exact Primary Keyword 机械拼进标题，也不要复制具体执行方案。\\n",
        1,
    )
    text = text.replace(
        "5. seo_title必须自然包含 exact Primary Keyword；去掉原稿里不适合公开的具体候选数字或操作承诺。\\n",
        "5. seo_title是公开改写阶段的工作标题；最终标题会在公开正文完成后重新生成3-5个候选并过Title SEO Gate。Primary Keyword字段保持不变，但最终标题不要求逐字包含，也不要求以‘分分彩’开头。\\n",
        1,
    )
    old = '''    if str(package.get("primary_keyword") or "") not in str(package.get("seo_title") or ""):\n        errors.append("seo_title_missing_primary_keyword")\n'''
    new = '''    title_review = package.get("title_review") or {}\n    if package.get("title_seo_contract_version") and title_review.get("passed") is not True:\n        errors.append("title_seo_gate_failed")\n'''
    if new not in text:
        if old not in text:
            raise RuntimeError("public safety exact keyword anchor missing")
        text = text.replace(old, new, 1)
    # Strip parent's title metadata before making a new public-r1 editorial title surface.
    old_fields = '''            "angle_contract_verified", "angle_approval_passed",\n        ):\n'''
    new_fields = '''            "angle_contract_verified", "angle_approval_passed",\n            "title_candidates", "title_selection_reason", "title_review", "title_seo_contract_version",\n        ):\n'''
    if new_fields not in text:
        if old_fields not in text:
            raise RuntimeError("public release field-strip anchor missing")
        text = text.replace(old_fields, new_fields, 1)
    anchor = '''        revision["claim_evidence"] = _sanitize_claims(\n            list(patch.get("claim_evidence") or []), list(parent.get("rule_refs") or [])\n        )\n'''
    addition = anchor + '''        title_review = apply_title_seo(revision, evidence_source=parent)\n        revision["title_review"] = title_review.as_dict()\n        if not title_review.passed:\n            last_errors = ["title_seo:" + error for error in title_review.errors]\n            payload["input"] += (\n                "\\n上一次公开版标题未通过Title SEO Gate：" + ", ".join(last_errors)\n                + "。请保持正文真实主题，不要添加无依据数字或夸张承诺。"\n            )\n            continue\n'''
    if "title_review = apply_title_seo(revision, evidence_source=parent)" not in text:
        if anchor not in text:
            raise RuntimeError("public release title selection anchor missing")
        text = text.replace(anchor, addition, 1)
    write(path, text)


def patch_public_revision_validation() -> None:
    path = "engine/public_release_revision.py"
    text = read(path)
    if "from .title_seo import validate_title_contract_fields" not in text:
        text = text.replace(
            "from .text import sha256_text\n",
            "from .text import sha256_text\nfrom .title_seo import validate_title_contract_fields\n",
            1,
        )
    anchor = '''    if package.get("revision_kind") != REVISION_KIND:\n        raise PublicReleaseRevisionError(f"revision_kind must be {REVISION_KIND}")\n'''
    addition = anchor + '''    if package.get("title_seo_contract_version"):\n        title_errors = validate_title_contract_fields(package)\n        if title_errors:\n            raise PublicReleaseRevisionError("Title SEO contract invalid: " + "; ".join(title_errors))\n        if (package.get("title_review") or {}).get("passed") is not True:\n            raise PublicReleaseRevisionError("Title SEO review must pass before public-r1 staging")\n'''
    if "Title SEO review must pass before public-r1 staging" not in text:
        if anchor not in text:
            raise RuntimeError("public revision title anchor missing")
        text = text.replace(anchor, addition, 1)
    write(path, text)


def patch_audit_cli() -> None:
    path = "scripts/title_seo_audit.py"
    target = ROOT / path
    if not target.exists():
        target.write_text(
            '''from engine.title_seo import write_title_audit\n\n\nif __name__ == "__main__":\n    report = write_title_audit()\n    print({\n        "formal_public_release_count": report["formal_public_release_count"],\n        "titles_starting_with_fenfen": report["titles_starting_with_fenfen"],\n        "titles_recommended_for_revision": report["titles_recommended_for_revision"],\n        "titles_with_high_similarity": report["titles_with_high_similarity"],\n        "titles_with_unsupported_numeric_claims": report["titles_with_unsupported_numeric_claims"],\n    })\n''',
            encoding="utf-8",
            newline="\n",
        )


def main() -> None:
    patch_title_runtime()
    patch_generation_normalization()
    patch_production_controller()
    patch_ai_prompt()
    patch_approval()
    patch_creator_first()
    patch_formal_inventory()
    patch_public_release()
    patch_public_revision_validation()
    patch_audit_cli()

    # Import only after all source patches are on disk.
    from engine.title_seo import write_title_audit
    report = write_title_audit(root=ROOT)
    print({
        "formal_public_release_count": report["formal_public_release_count"],
        "titles_starting_with_fenfen": report["titles_starting_with_fenfen"],
        "titles_recommended_for_revision": report["titles_recommended_for_revision"],
        "titles_with_high_similarity": report["titles_with_high_similarity"],
        "titles_with_unsupported_numeric_claims": report["titles_with_unsupported_numeric_claims"],
    })


if __name__ == "__main__":
    main()
