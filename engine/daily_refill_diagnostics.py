"""Bounded, content-free diagnostics; never copy error text or dynamic keys."""
from collections import Counter


def error_category(value: object) -> str:
    # Match only known producer prefixes; never persist their dynamic suffixes.
    if not isinstance(value, str):
        return "unclassified"
    for prefix, category in (
        ("model provider HTTP 429:", "provider_rate_limited"),
        ("model provider HTTP 401:", "provider_authentication"),
        ("model provider HTTP 403:", "provider_authorization"),
        ("model provider HTTP ", "provider_http"),
        ("model provider transport failed:", "provider_transport"),
        ("model provider returned non-JSON response", "provider_response_format"),
        ("model response error:", "provider_response_error"),
        ("model response not completed:", "provider_incomplete"),
        ("model response refused:", "provider_refusal"),
        ("model response contains no output_text", "provider_empty_output"),
        ("structured model output", "structured_output"),
        ("generated article violated immutable contract:", "immutable_contract"),
        ("[V2.2]", "multistage_gate"),
        ("claim_evidence[", "claim_evidence_gate"),
        ("hard claim sentence lacks claim_evidence:", "claim_evidence_gate"),
        ("practical_guidance", "editorial_gate"),
        ("article_angle_contract", "angle_contract_gate"),
        ("angle_delivery", "angle_contract_gate"),
        ("mechanics_case ", "angle_delivery_gate"),
        ("space_math ", "angle_delivery_gate"),
        ("execution_checklist ", "angle_delivery_gate"),
        ("parameter_boundary ", "angle_delivery_gate"),
        ("multistage_order ", "angle_delivery_gate"),
        ("sample_provenance ", "angle_delivery_gate"),
        ("title_seo_contract_version", "title_seo_gate"),
        ("title_candidates ", "title_seo_gate"),
        ("title_selection_reason ", "title_seo_gate"),
        ("title and seo_title ", "title_seo_gate"),
        ("duplicate risk:", "duplicate_gate"),
        ("structural duplicate risk:", "duplicate_gate"),
        ("guaranteed-outcome language:", "compliance_gate"),
        ("forbidden guaranteed-outcome term:", "compliance_gate"),
        ("bet compliance failed:", "compliance_gate"),
        ("reader-facing FFC article", "terminology_gate"),
        ("public release safety gate failed:", "public_release_gate"),
        ("POLICY_INVARIANT_VIOLATION", "policy_invariant"),
        ("MODEL_PROVIDER_API_KEY is not configured", "missing_provider_key"),
    ):
        if value.startswith(prefix):
            return category
    return "unclassified"


def controller_diagnostics(result: dict) -> dict:
    outcomes = Counter()
    errors = Counter()
    allowed = {
        "staged", "unchanged", "pre_generation_duplicate_blocked",
        "generation_failed", "rejected_multistage", "rejected",
        "rejected_for_revision", "reader_terminology_rejected", "formal_inventory_error",
    }
    for row in result.get("results", []):
        status = row.get("status")
        outcomes[status if isinstance(status, str) and status in allowed else "unknown"] += 1
        messages = row.get("errors")
        messages = list(messages) if isinstance(messages, (list, tuple)) else []
        if row.get("error") is not None:
            messages.append(row["error"])
        for message in messages:
            errors[error_category(message)] += 1
    return {
        "outcome_counts": dict(outcomes),
        "result_rows": sum(outcomes.values()),
        "error_category_counts": dict(errors),
        "error_observations": sum(errors.values()),
        # multistage_failed is a subset of approval_failed, not additive to it.
        **{key: int(result.get(key) or 0) for key in (
            "multistage_failed", "reader_terminology_failed",
            "formal_inventory_error_count", "formal_inventory_unchanged",
            "pre_generation_duplicate_blocked",
        )},
    }


def select_candidates(rows, attempted_ids, frozen, policy, limit, keyword_allowed):
    """Observe the existing ordered, first-match filters without changing them."""
    counts = dict.fromkeys((
        "input", "examined", "missing_article_id", "already_attempted",
        "frozen", "keyword_blocked", "selected", "not_examined",
    ), 0)
    counts["input"] = len(rows)
    selected = []
    for row in rows:
        counts["examined"] += 1
        blueprint = row.get("blueprint") or {}
        article_id = str(blueprint.get("article_id") or "")
        if not article_id:
            counts["missing_article_id"] += 1
            continue
        if article_id in attempted_ids:
            counts["already_attempted"] += 1
            continue
        if article_id in frozen:
            counts["frozen"] += 1
            continue
        if not keyword_allowed(str(blueprint.get("primary_keyword") or ""), policy):
            counts["keyword_blocked"] += 1
            continue
        selected.append(row)
        counts["selected"] += 1
        if len(selected) >= limit:
            break
    counts["not_examined"] = counts["input"] - counts["examined"]
    return selected, counts
