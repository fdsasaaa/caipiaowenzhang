from __future__ import annotations

import re
from copy import deepcopy


class RealKnowledgeEvidenceNormalizationError(ValueError):
    pass


def _compact(value: str) -> str:
    return re.sub(r"[\s。！？!?]+", "", str(value or ""))


def normalize_real_knowledge_claim_metadata(packet: dict, article: dict) -> dict:
    """Repair only evidence metadata that is deterministically owned by this contract.

    This function never changes article content. It is intentionally narrower
    than the generic claim gate: only the exact source/parameter boundary and an
    exact aggregate pipeline-exclusion calculation may be canonicalized.
    """
    contract = packet.get("real_knowledge_validation") or {}
    if not contract:
        raise RealKnowledgeEvidenceNormalizationError("real_knowledge_validation contract missing")

    normalized = deepcopy(article)
    entries = normalized.get("claim_evidence")
    if not isinstance(entries, list):
        raise RealKnowledgeEvidenceNormalizationError("claim_evidence must be a list")

    boundary = str(contract.get("required_source_parameter_boundary") or "")
    source_refs = list(contract.get("source_refs") or [])
    rules = list(packet.get("immutable_facts", {}).get("rule_refs") or [])
    result = packet.get("practicality", {}).get("filter_pipeline_result") or {}
    total_excluded = result.get("total_excluded")
    if not boundary or not source_refs or not rules or not isinstance(total_excluded, int):
        raise RealKnowledgeEvidenceNormalizationError("locked real-knowledge evidence inputs are incomplete")

    allowed_total_claims = {
        f"整体共排除{total_excluded}个",
        f"整体总共排除{total_excluded}个",
        f"总共排除{total_excluded}个",
        f"总排除{total_excluded}个",
    }

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        claim = str(entry.get("claim_text") or "")

        if claim == boundary and entry.get("support_type") == "source_unverified":
            # The body already states that the research parameters are not from
            # the source and do not prove predictive advantage. Preserve that
            # exact content sentence; qualify the evidence record explicitly so
            # the source-unverified gate does not mistake a boundary statement
            # for an asserted source fact.
            entry["claim_text"] = "来源内容未独立验证；" + boundary
            entry["claim_type"] = "source_claim"
            entry["support_type"] = "source_unverified"
            entry["support_refs"] = source_refs
            entry["evidence_note"] = (
                str(entry.get("evidence_note") or "")
                + " [system-normalized: explicit unverified-source qualifier for source/parameter boundary]"
            ).strip()
            continue

        if (
            entry.get("claim_type") == "calculation"
            and entry.get("support_type") == "synthetic_case"
            and _compact(claim) in allowed_total_claims
        ):
            # This number is not a synthetic sample fact. It is exactly
            # starting_space - final_space from the frozen filter_pipeline.
            entry["support_type"] = "verified_rule"
            entry["support_refs"] = rules
            entry["evidence_note"] = (
                str(entry.get("evidence_note") or "")
                + " [system-normalized: exact aggregate filter_pipeline exclusion]"
            ).strip()

    return normalized
