from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .ai_generation import GenerationError, _response_output_text
from .formal_approved_inventory import stage_formal_approved_package
from .production_controller import build_production_plan, execute_production_plan
from .provider_transport import (
    DEFAULT_OPENAI_BASE_URL,
    make_responses_transport,
    models_endpoint,
    request_json,
    responses_endpoint,
)
from .public_release_revision import (
    expected_public_release_fingerprint,
    stage_public_release_revision,
    validate_public_release_revision,
    write_public_release_manifest,
)
from .public_terminology import audit_article
from .store import ROOT
from .text import sha256_text

POLICY_PATH = ROOT / "policies" / "DAILY_WEBSITE_READY_PRODUCTION.json"
REPORT_ROOT = ROOT / "artifacts" / "daily_website_ready"


class DailyProductionError(RuntimeError):
    pass


def load_daily_policy(path: Path | None = None) -> dict:
    data = json.loads((path or POLICY_PATH).read_text(encoding="utf-8"))
    for field in ("target", "minimum", "maximum", "candidate_pool", "timezone"):
        if field not in data:
            raise DailyProductionError(f"daily policy missing {field}")
    minimum = int(data["minimum"])
    target = int(data["target"])
    maximum = int(data["maximum"])
    if not (1 <= minimum <= target <= maximum):
        raise DailyProductionError("daily volume band must satisfy 1 <= minimum <= target <= maximum")
    if int(data["candidate_pool"]) < target:
        raise DailyProductionError("candidate_pool must be at least target")
    return data


def production_date(now: datetime | None, timezone_name: str) -> str:
    zone = ZoneInfo(timezone_name)
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(zone).date().isoformat()


def _batch_id(day: str) -> str:
    return "DAILY-" + day.replace("-", "")


def _model_ids(payload: dict) -> list[str]:
    rows = payload.get("data") or []
    return [str(row.get("id")) for row in rows if isinstance(row, dict) and row.get("id")]


def choose_model(api_key: str, base_url: str | None, requested: str | None, hints: list[str]) -> str:
    if requested:
        return requested
    payload = request_json(models_endpoint(base_url), api_key=api_key, timeout=30)
    models = _model_ids(payload)
    for hint in hints:
        for model in models:
            if hint.lower() in model.lower():
                return model
    if models:
        return models[0]
    raise DailyProductionError("provider /models returned no usable model ids")


def _public_release_schema() -> dict:
    claim = {
        "type": "object",
        "additionalProperties": False,
        "required": ["claim_text", "claim_type", "support_type", "support_refs", "evidence_note"],
        "properties": {
            "claim_text": {"type": "string"},
            "claim_type": {"type": "string", "enum": ["rule_fact", "calculation", "methodology", "editorial"]},
            "support_type": {"type": "string", "enum": ["verified_rule", "synthetic_case", "editorial"]},
            "support_refs": {"type": "array", "items": {"type": "string"}},
            "evidence_note": {"type": "string"},
        },
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["content", "seo_title", "meta_description", "search_intent", "summary", "claim_evidence"],
        "properties": {
            "content": {"type": "string"},
            "seo_title": {"type": "string"},
            "meta_description": {"type": "string"},
            "search_intent": {"type": "string"},
            "summary": {"type": "string"},
            "claim_evidence": {"type": "array", "items": claim},
        },
    }


def _public_release_prompt(parent: dict) -> str:
    compact = {
        key: parent.get(key)
        for key in (
            "article_id", "title", "seo_title", "primary_keyword", "secondary_keywords",
            "search_intent", "summary", "subject_lottery", "subject_play", "lottery",
            "play", "rule_refs", "source_refs", "case_scope", "content",
        )
    }
    return (
        "你是网站公开版编辑器。下面是已通过内部验证的 Approved parent。"
        "请把它改写为可公开发布、教育/研究导向的版本，只返回结构化JSON。"
        "必须保留玩法机制、文章主题和 exact Primary Keyword 的搜索意图，但不要复制具体执行方案。\n"
        "公开版硬规则：\n"
        "1. 不提供具体候选号码、数字池、逐期选号、下一期建议、跟投/追号/倍投/加倍/资金递进/回本/止损等执行指令。\n"
        "2. 不提供具体下注金额、倍数、投注路径，不把历史结构写成未来预测优势，不承诺收益、胜率或稳定盈利。\n"
        "3. 可以解释组合数学、规则机制、参数预注册、历史复盘、样本外验证、随机波动和常见误区。\n"
        "4. content 使用简单中文HTML，至少3个h2短章节和多个短段落；不得使用script/iframe/form/object/embed。\n"
        "5. seo_title必须自然包含 exact Primary Keyword；去掉原稿里不适合公开的具体候选数字或操作承诺。\n"
        "6. claim_evidence只登记公开正文实际存在的硬声明。verified_rule只能引用parent.rule_refs；"
        "synthetic_case只能引用case_bundle；纯范围/风险说明用editorial且support_refs=[]。\n"
        "7. 至少明确一次：结构分类或历史样本表现不能单独证明未来预测优势。\n\n"
        "Approved parent JSON:\n"
        + json.dumps(compact, ensure_ascii=False, separators=(",", ":"))
    )


def _sanitize_claims(claims: list[dict], rule_refs: list[str]) -> list[dict]:
    allowed_rules = set(str(x) for x in rule_refs)
    cleaned: list[dict] = []
    for row in claims:
        if not isinstance(row, dict):
            continue
        support_type = str(row.get("support_type") or "")
        refs = [str(x) for x in row.get("support_refs") or []]
        if support_type == "verified_rule":
            if not refs or any(ref not in allowed_rules for ref in refs):
                continue
        elif support_type == "synthetic_case":
            if refs != ["case_bundle"]:
                continue
        elif support_type == "editorial":
            refs = []
        else:
            continue
        claim_text = str(row.get("claim_text") or "").strip()
        if not claim_text:
            continue
        cleaned.append({
            "claim_text": claim_text,
            "claim_type": str(row.get("claim_type") or "editorial"),
            "support_type": support_type,
            "support_refs": refs,
            "evidence_note": str(row.get("evidence_note") or "").strip(),
        })
    return cleaned


def public_safety_errors(package: dict, policy: dict) -> list[str]:
    content = str(package.get("content") or "")
    errors: list[str] = []
    lowered = content.lower()
    for token in ("<script", "<iframe", "<form", "<object", "<embed"):
        if token in lowered:
            errors.append(f"forbidden_html:{token}")
    for pattern in policy.get("forbidden_public_content_patterns", []):
        if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            errors.append(f"operational_pattern:{pattern}")
    plain = re.sub(r"<[^>]+>", "", content)
    if len(plain.strip()) < int(policy.get("public_release_min_plain_chars") or 500):
        errors.append("public_release_too_short")
    if len(re.findall(r"<h2(?:\s[^>]*)?>", content, re.IGNORECASE)) < int(policy.get("public_release_min_h2") or 3):
        errors.append("public_release_too_few_sections")
    uncertainty_terms = [str(x) for x in policy.get("required_uncertainty_terms_any", [])]
    if uncertainty_terms and not any(term in content for term in uncertainty_terms):
        errors.append("missing_uncertainty_boundary")
    if str(package.get("primary_keyword") or "") not in str(package.get("seo_title") or ""):
        errors.append("seo_title_missing_primary_keyword")
    if package.get("content_hash") == package.get("parent_content_hash"):
        errors.append("public_release_content_unchanged")
    terminology = audit_article(f"daily-public:{package.get('article_id')}", package)
    errors.extend(f"terminology:{row.message}" for row in terminology if row.severity == "error")
    return errors


def generate_public_release(parent: dict, *, api_key: str, base_url: str, model: str, policy: dict) -> dict:
    payload = {
        "model": model,
        "store": False,
        "input": _public_release_prompt(parent),
        "text": {
            "format": {
                "type": "json_schema",
                "name": "daily_website_public_release_v1",
                "strict": True,
                "schema": _public_release_schema(),
            }
        },
    }
    attempts = max(1, int(policy.get("public_release_generation_attempts") or 2))
    last_errors: list[str] = []
    for _ in range(attempts):
        response = request_json(
            responses_endpoint(base_url),
            api_key=api_key,
            payload=payload,
            timeout=int(policy.get("public_release_timeout_seconds") or 180),
        )
        try:
            patch = json.loads(_response_output_text(response))
        except json.JSONDecodeError:
            last_errors = ["public_release_output_not_json"]
            payload["input"] += "\n上一次输出无法解析为JSON，请严格按Schema重做。"
            continue
        if not isinstance(patch, dict):
            last_errors = ["public_release_output_not_object"]
            continue

        revision = dict(parent)
        for field in (
            "practical_guidance", "editorial_contract_version", "angle_delivery",
            "article_angle_contract", "article_angle_contract_version",
            "angle_contract_verified", "angle_approval_passed",
        ):
            revision.pop(field, None)
        revision["content"] = str(patch.get("content") or "").strip()
        revision["seo_title"] = str(patch.get("seo_title") or "").strip()
        revision["title"] = revision["seo_title"]
        revision["meta_description"] = str(patch.get("meta_description") or "").strip()
        revision["search_intent"] = str(patch.get("search_intent") or "").strip()
        revision["summary"] = str(patch.get("summary") or "").strip()
        revision["claim_evidence"] = _sanitize_claims(
            list(patch.get("claim_evidence") or []), list(parent.get("rule_refs") or [])
        )
        revision["content_hash"] = sha256_text(revision["content"])
        revision["approved_at"] = datetime.now(timezone.utc).isoformat()
        revision["source_batch_id"] = str(parent.get("creator_batch_id") or "")
        revision["revision_kind"] = "website_public_release"
        revision["release_revision"] = 1
        revision["revision_id"] = f"{parent['article_id']}:public-r1"
        revision["parent_content_hash"] = parent["content_hash"]
        revision["parent_fingerprint"] = parent["fingerprint"]
        revision["public_release_review"] = {
            "status": "approved",
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
            "review_contract": "website-public-release-editorial-v1",
        }
        revision["fingerprint"] = expected_public_release_fingerprint(revision)
        last_errors = public_safety_errors(revision, policy)
        if not last_errors:
            validate_public_release_revision(revision)
            return revision
        payload["input"] += (
            "\n上一次公开版被本地质量/安全门禁拒绝，原因："
            + ", ".join(last_errors)
            + "。请保持主题与Primary Keyword，但重新改写并消除这些问题。"
        )
    raise DailyProductionError("public release safety gate failed: " + ", ".join(last_errors))


def _keyword_allowed(keyword: str, policy: dict) -> bool:
    normalized = str(keyword or "").strip().lower()
    if not normalized:
        return False
    blocked_exact = {str(x).strip().lower() for x in policy.get("blocked_exact_primary_keywords", [])}
    if normalized in blocked_exact:
        return False
    return not any(
        str(fragment).strip().lower() in normalized
        for fragment in policy.get("blocked_primary_keyword_fragments", [])
        if str(fragment).strip()
    )


def _write_report(day: str, payload: dict) -> Path:
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    target = REPORT_ROOT / f"{day}.json"
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


def run_daily(*, now: datetime | None = None, policy_path: Path | None = None) -> dict:
    policy = load_daily_policy(policy_path)
    day = production_date(now, str(policy["timezone"]))
    report_path = REPORT_ROOT / f"{day}.json"
    if report_path.is_file():
        prior = json.loads(report_path.read_text(encoding="utf-8"))
        if prior.get("status") in {"PASS_TARGET", "PASS_PARTIAL_QUALITY_FIRST"}:
            return {"status": "ALREADY_COMPLETED", "date": day, "report_path": str(report_path)}

    api_key = os.getenv("OPENAI_API_KEY") or ""
    if not api_key:
        raise DailyProductionError("MODEL_PROVIDER_API_KEY is not configured")
    base_url = (os.getenv("OPENAI_BASE_URL") or DEFAULT_OPENAI_BASE_URL).strip()
    model = choose_model(
        api_key,
        base_url,
        (os.getenv("OPENAI_MODEL") or "").strip() or None,
        [str(x) for x in policy.get("model_preference_hints", ["mini", "flash", "small", "lite"])],
    )
    batch_id = _batch_id(day)
    target = int(policy["target"])
    minimum = int(policy["minimum"])
    maximum = int(policy["maximum"])

    plan = build_production_plan(
        target,
        provider_id="",
        batch_size=int(policy.get("internal_batch_size") or 20),
    )
    frozen = set(str(x) for x in policy.get("frozen_article_ids", []))
    candidates = []
    for row in plan.get("candidates", []):
        blueprint = row.get("blueprint") or {}
        if str(blueprint.get("article_id") or "") in frozen:
            continue
        if not _keyword_allowed(str(blueprint.get("primary_keyword") or ""), policy):
            continue
        candidates.append(row)
        if len(candidates) >= int(policy["candidate_pool"]):
            break
    plan["candidates"] = candidates
    plan["attempt_budget"] = len(candidates)
    plan["target_new_formal_articles"] = target

    def stage_with_batch(package: dict) -> dict:
        enriched = dict(package)
        enriched["creator_batch_id"] = batch_id
        enriched.setdefault("creator_first_contract_version", "1.0")
        return stage_formal_approved_package(enriched)

    result = execute_production_plan(
        plan,
        model=model,
        api_key=api_key,
        transport=make_responses_transport(base_url),
        stage_fn=stage_with_batch,
    )
    staged_ids = [
        str(row["article_id"])
        for row in result.get("results", [])
        if row.get("status") == "staged" and row.get("article_id")
    ][:maximum]

    public_ready: list[dict] = []
    public_failed: list[dict] = []
    for article_id in staged_ids:
        parent_path = ROOT / "articles" / "approved" / f"{article_id}.json"
        parent = json.loads(parent_path.read_text(encoding="utf-8"))
        try:
            revision = generate_public_release(
                parent, api_key=api_key, base_url=base_url, model=model, policy=policy
            )
            staged_release = stage_public_release_revision(revision)
            public_ready.append({
                "article_id": article_id,
                "primary_keyword": parent.get("primary_keyword"),
                "path": staged_release.get("path"),
                "revision_id": staged_release.get("revision_id"),
            })
        except (DailyProductionError, GenerationError, ValueError) as exc:
            public_failed.append({"article_id": article_id, "error": str(exc)})

    ready_count = len(public_ready)
    if ready_count >= target:
        status = "PASS_TARGET"
    elif ready_count >= minimum:
        status = "PASS_PARTIAL_QUALITY_FIRST"
    else:
        status = "BLOCKED_BELOW_MINIMUM"

    manifest = None
    if ready_count >= minimum:
        manifest = write_public_release_manifest(batch_id, expected_count=ready_count)

    report = {
        "schema_version": 1,
        "date": day,
        "timezone": policy["timezone"],
        "batch_id": batch_id,
        "status": status,
        "target": target,
        "minimum": minimum,
        "maximum": maximum,
        "candidate_pool_limit": int(policy["candidate_pool"]),
        "model": model,
        "base_url": base_url,
        "approved_staged": len(staged_ids),
        "website_ready_public_r1": ready_count,
        "public_release_failed": public_failed,
        "production_stop_reason": result.get("stop_reason"),
        "production_status": result.get("status"),
        "quality_score_average": result.get("quality_score_average"),
        "editorial_score_average": result.get("editorial_score_average"),
        "article_angle_distribution": result.get("article_angle_distribution"),
        "play_distribution": result.get("play_distribution"),
        "manifest": manifest,
        "website_sync_attempted": False,
        "scheduled": False,
        "published": False,
        "quality_floor_lowered": False,
        "public_ready": public_ready,
    }
    _write_report(day, report)
    if ready_count < minimum:
        raise DailyProductionError(
            f"quality-first minimum not met: website_ready={ready_count}, minimum={minimum}"
        )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Daily quality-first website-ready article production")
    parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    args = parser.parse_args()
    try:
        result = run_daily(policy_path=args.policy)
    except (DailyProductionError, GenerationError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 7
    print(json.dumps({"ok": True, **result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
