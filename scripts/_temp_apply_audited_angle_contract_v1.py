from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    assert old in text, f"marker missing in {path}: {old[:120]!r}"
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


# planner.py — default behavior unchanged; production may request used base plans
# so unused audited angles remain resumable after mechanics_case is staged.
replace_once(
    "engine/planner.py",
    "def plan_articles(provider_id: str, lottery: str, play: str, count: int = 10) -> dict:\n",
    "def plan_articles(\n    provider_id: str, lottery: str, play: str, count: int = 10, *, include_used_angles: bool = False\n) -> dict:\n",
)
replace_once(
    "engine/planner.py",
    "            if angle_hash in used or angle_hash in seen_new:\n                continue\n",
    "            if ((not include_used_angles and angle_hash in used) or angle_hash in seen_new):\n                continue\n",
)

# blueprints.py — production can build a neutral base blueprint and apply registry
# ownership only after deterministic article-angle expansion.
replace_once(
    "engine/blueprints.py",
    "def blueprint_from_plan(plan: dict) -> dict:\n",
    "def blueprint_from_plan(plan: dict, *, apply_registry_gates: bool = True) -> dict:\n",
)
replace_once(
    "engine/blueprints.py",
    "    keyword_hits = keyword_owners(primary_keyword, exclude_article_id=blueprint[\"article_id\"])\n",
    "    if not apply_registry_gates:\n        return blueprint\n\n    keyword_hits = keyword_owners(primary_keyword, exclude_article_id=blueprint[\"article_id\"])\n",
)

# dedup.py — expose the exact existing lexical score for candidate-pool preflight.
replace_once(
    "engine/dedup.py",
    "from .text import jaccard\n",
    "from .text import jaccard\n\nLEXICAL_DUPLICATE_THRESHOLD = 0.72\n",
)
replace_once(
    "engine/dedup.py",
    "def duplicate_candidates(candidate: dict, threshold: float = 0.72) -> list[DuplicateHit]:\n",
    "def lexical_similarity(candidate: dict, old: dict) -> float:\n    if candidate.get(\"fingerprint\") and candidate.get(\"fingerprint\") == old.get(\"fingerprint\"):\n        return 1.0\n    return jaccard(_core(candidate), _core(old))\n\n\ndef duplicate_candidates(candidate: dict, threshold: float = LEXICAL_DUPLICATE_THRESHOLD) -> list[DuplicateHit]:\n",
)
replace_once(
    "engine/dedup.py",
    "        old_core = _core(old)\n        score = jaccard(candidate_core, old_core)\n",
    "        score = lexical_similarity(candidate, old)\n",
)

# semantic_dedup.py — angle identity is a first-class 20% structural dimension
# only when BOTH records carry a verified v1 contract. Approved owners additionally
# need angle_approval_passed=True; legacy/uncontracted scoring stays byte-for-byte
# equivalent to the old weights.
replace_once(
    "engine/semantic_dedup.py",
    "from .store import iter_registry\n",
    "from .article_angles import AUDITED_ANGLE_STRUCTURAL_WEIGHT, same_audited_angle\nfrom .store import iter_registry\n\nSTRUCTURAL_DUPLICATE_THRESHOLD = 0.82\n",
)
replace_once(
    "engine/semantic_dedup.py",
    "    return min(1.0, score), reasons\n\n\ndef structural_duplicate_candidates(candidate: dict, threshold: float = 0.82) -> list[StructuralDuplicateHit]:\n",
    "    base_score = min(1.0, score)\n    same_angle = same_audited_angle(candidate, old)\n    if same_angle is None:\n        return base_score, reasons\n    weight = AUDITED_ANGLE_STRUCTURAL_WEIGHT\n    if same_angle:\n        reasons.append(\"same_audited_information_gain\")\n        return min(1.0, (1.0 - weight) * base_score + weight), reasons\n    reasons.append(\"different_audited_information_gain\")\n    return min(1.0, (1.0 - weight) * base_score), reasons\n\n\ndef structural_duplicate_candidates(\n    candidate: dict, threshold: float = STRUCTURAL_DUPLICATE_THRESHOLD\n) -> list[StructuralDuplicateHit]:\n",
)

# draft_packets.py — make the angle contract immutable and require a structured
# angle_delivery from the model only for contracted articles.
replace_once(
    "engine/draft_packets.py",
    "    editorial_contract_version = blueprint.get(\"editorial_contract_version\")\n",
    "    editorial_contract_version = blueprint.get(\"editorial_contract_version\")\n    article_angle_contract_version = blueprint.get(\"article_angle_contract_version\")\n    article_angle_contract = blueprint.get(\"article_angle_contract\")\n",
)
replace_once(
    "engine/draft_packets.py",
    "    if editorial_contract_version:\n        required_fields.extend([\"editorial_contract_version\", \"practical_guidance\"])\n",
    "    if editorial_contract_version:\n        required_fields.extend([\"editorial_contract_version\", \"practical_guidance\"])\n    if article_angle_contract_version:\n        required_fields.extend([\"article_angle_contract_version\", \"information_gain_type\", \"angle_delivery\"])\n",
)
replace_once(
    "engine/draft_packets.py",
    "            \"information_gain_type\": blueprint.get(\"information_gain_type\"),\n",
    "            \"information_gain_type\": blueprint.get(\"information_gain_type\"),\n            \"angle_signature\": blueprint.get(\"angle_signature\"),\n            \"article_angle_contract_version\": article_angle_contract_version,\n            \"angle_contract_verified\": bool(blueprint.get(\"angle_contract_verified\")),\n",
)
replace_once(
    "engine/draft_packets.py",
    "    if editorial_contract_version:\n        packet[\"editorial_contract_version\"] = editorial_contract_version\n",
    "    if article_angle_contract_version:\n        if not isinstance(article_angle_contract, dict) or not article_angle_contract:\n            raise ValueError(\"contracted blueprint requires article_angle_contract\")\n        packet[\"article_angle_contract_version\"] = article_angle_contract_version\n        packet[\"article_angle_contract\"] = dict(article_angle_contract)\n    if editorial_contract_version:\n        packet[\"editorial_contract_version\"] = editorial_contract_version\n",
)

# ai_generation.py — structured angle_delivery and immutable angle identity.
replace_once(
    "engine/ai_generation.py",
    "def article_output_schema(packet: dict | None = None) -> dict:\n",
    '''def _angle_delivery_schema(packet: dict) -> dict:\n    contract = packet.get("article_angle_contract") or {}\n    facts = contract.get("required_machine_facts") or {}\n    return {\n        "type": "object",\n        "additionalProperties": False,\n        "required": [\n            "angle_type", "reader_question", "deliverable_summary",\n            "starting_space", "final_space", "excluded_space", "stage_count",\n            "stage_labels", "sample_stage_labels", "static_stage_labels", "evidence_mode",\n            "parameter_owner", "source_parameter_attribution_allowed",\n            "predictive_advantage_claimed", "stop_after_final_stage",\n        ],\n        "properties": {\n            "angle_type": {"type": "string", "enum": [str(contract.get("angle_type") or "")]},\n            "reader_question": {"type": "string", "enum": [str(contract.get("reader_question") or "")]},\n            "deliverable_summary": {"type": "string"},\n            "starting_space": {"type": "integer"},\n            "final_space": {"type": "integer"},\n            "excluded_space": {"type": "integer"},\n            "stage_count": {"type": "integer"},\n            "stage_labels": {"type": "array", "items": {"type": "string"}},\n            "sample_stage_labels": {"type": "array", "items": {"type": "string"}},\n            "static_stage_labels": {"type": "array", "items": {"type": "string"}},\n            "evidence_mode": {"type": "string", "enum": [str(facts.get("evidence_mode") or "")]},\n            "parameter_owner": {"type": "string", "enum": ["system_research"]},\n            "source_parameter_attribution_allowed": {"type": "boolean", "enum": [False]},\n            "predictive_advantage_claimed": {"type": "boolean", "enum": [False]},\n            "stop_after_final_stage": {"type": "boolean", "enum": [True]},\n        },\n    }\n\n\ndef article_output_schema(packet: dict | None = None) -> dict:\n''',
)
replace_once(
    "engine/ai_generation.py",
    "        properties[\"practical_guidance\"] = _practical_guidance_schema()\n",
    "        properties[\"practical_guidance\"] = _practical_guidance_schema()\n    if packet and packet.get(\"article_angle_contract_version\"):\n        contract = packet.get(\"article_angle_contract\") or {}\n        required.extend([\"article_angle_contract_version\", \"information_gain_type\", \"angle_delivery\"])\n        properties[\"article_angle_contract_version\"] = {\n            \"type\": \"string\", \"enum\": [str(packet[\"article_angle_contract_version\"])]\n        }\n        properties[\"information_gain_type\"] = {\n            \"type\": \"string\", \"enum\": [str(contract.get(\"angle_type\") or \"\")]\n        }\n        properties[\"angle_delivery\"] = _angle_delivery_schema(packet)\n",
)
replace_once(
    "engine/ai_generation.py",
    "    display_term_rules = \"\"\n",
    "    angle_rules = \"\"\n    angle_contract = packet.get(\"article_angle_contract\") or {}\n    if packet.get(\"article_angle_contract_version\") and angle_contract:\n        angle_rules = (\n            \"20. article_angle_contract 是本篇独立信息增益合同，不是SEO装饰。正文必须围绕 reader_question 和 required_deliverable 展开，不能退回成通用技巧介绍。\\n\"\n            \"21. 必须输出 angle_delivery，并逐字复制 angle_type/reader_question；starting_space/final_space/excluded_space/stage_count、stage_labels、sample/static stage labels 和 evidence_mode 必须与合同机器事实完全一致。\\n\"\n            \"22. parameter_owner 必须是 system_research；source_parameter_attribution_allowed=false；predictive_advantage_claimed=false；stop_after_final_stage=true。\\n\"\n            \"23. 不同 angle 有不同交付：space_math 必须把候选空间数学算清；execution_checklist 必须形成可执行步骤清单；parameter_boundary 必须明确系统参数与来源/样本边界；multistage_order 必须按合同顺序逐层解释；sample_provenance 必须明确演示样本不构成预测；mechanics_case 必须完成可复算案例。\\n\"\n        )\n    display_term_rules = \"\"\n",
)
replace_once(
    "engine/ai_generation.py",
    "        + display_term_rules\n        + \"\\nDraft Packet:\\n\" + json.dumps(packet, ensure_ascii=False, sort_keys=True)\n",
    "        + display_term_rules\n        + angle_rules\n        + \"\\nDraft Packet:\\n\" + json.dumps(packet, ensure_ascii=False, sort_keys=True)\n",
)
replace_once(
    "engine/ai_generation.py",
    "    if packet.get(\"editorial_contract_version\"):\n        expected[\"editorial_contract_version\"] = packet.get(\"editorial_contract_version\")\n",
    "    if packet.get(\"editorial_contract_version\"):\n        expected[\"editorial_contract_version\"] = packet.get(\"editorial_contract_version\")\n    if packet.get(\"article_angle_contract_version\"):\n        contract = packet.get(\"article_angle_contract\") or {}\n        expected[\"article_angle_contract_version\"] = packet.get(\"article_angle_contract_version\")\n        expected[\"information_gain_type\"] = contract.get(\"angle_type\")\n",
)
replace_once(
    "engine/ai_generation.py",
    "    if errors:\n        raise GenerationError(\"generated article violated immutable contract: \" + \"; \".join(errors))\n",
    "    if packet.get(\"article_angle_contract_version\"):\n        contract = packet.get(\"article_angle_contract\") or {}\n        delivery = article.get(\"angle_delivery\") or {}\n        if delivery.get(\"angle_type\") != contract.get(\"angle_type\"):\n            errors.append(\"angle_delivery.angle_type differs from Draft Packet\")\n        if delivery.get(\"reader_question\") != contract.get(\"reader_question\"):\n            errors.append(\"angle_delivery.reader_question differs from Draft Packet\")\n    if errors:\n        raise GenerationError(\"generated article violated immutable contract: \" + \"; \".join(errors))\n",
)

# approval.py — angle gate participates in Approval and only passed contracts are
# persisted as auditable structural identity.
replace_once(
    "engine/approval.py",
    "from .article_memory import append_article_state, get_article_record\n",
    "from .article_angle_quality import evaluate_article_angle\nfrom .article_memory import append_article_state, get_article_record\n",
)
replace_once(
    "engine/approval.py",
    "    editorial_score: int = 100\n",
    "    editorial_score: int = 100\n    angle_score: int | None = None\n",
)
replace_once(
    "engine/approval.py",
    "        \"information_gain_type\": facts.get(\"information_gain_type\") or existing.get(\"information_gain_type\", \"method_mechanics_and_reproducible_case\"),\n",
    "        \"information_gain_type\": facts.get(\"information_gain_type\") or existing.get(\"information_gain_type\", \"method_mechanics_and_reproducible_case\"),\n        \"angle_signature\": facts.get(\"angle_signature\") or existing.get(\"angle_signature\"),\n        \"article_angle_contract_version\": facts.get(\"article_angle_contract_version\") or existing.get(\"article_angle_contract_version\"),\n        \"angle_contract_verified\": bool(facts.get(\"angle_contract_verified\") or existing.get(\"angle_contract_verified\")),\n",
)
replace_once(
    "engine/approval.py",
    "    if primary_cluster:\n        package[\"primary_seo_cluster_id\"] = primary_cluster\n",
    "    angle_contract = packet.get(\"article_angle_contract\") or {}\n    if packet.get(\"article_angle_contract_version\") and article.get(\"angle_approval_passed\") is True:\n        package[\"article_angle_contract_version\"] = packet[\"article_angle_contract_version\"]\n        package[\"information_gain_type\"] = angle_contract.get(\"angle_type\")\n        package[\"angle_signature\"] = facts.get(\"angle_signature\") or existing.get(\"angle_signature\")\n        package[\"angle_contract_verified\"] = True\n        package[\"angle_approval_passed\"] = True\n        package[\"article_angle_contract\"] = angle_contract\n        package[\"angle_delivery\"] = article.get(\"angle_delivery\") or {}\n    if primary_cluster:\n        package[\"primary_seo_cluster_id\"] = primary_cluster\n",
)
replace_once(
    "engine/approval.py",
    "        \"information_gain_type\": facts.get(\"information_gain_type\"),\n        \"content_hash\": sha256_text(article.get(\"content\", \"\")) if article.get(\"content\") else None,\n",
    "        \"information_gain_type\": facts.get(\"information_gain_type\"),\n        \"angle_signature\": facts.get(\"angle_signature\") or existing.get(\"angle_signature\"),\n        \"content_hash\": sha256_text(article.get(\"content\", \"\")) if article.get(\"content\") else None,\n",
)
replace_once(
    "engine/approval.py",
    "    if primary_cluster:\n        changes[\"primary_seo_cluster_id\"] = primary_cluster\n",
    "    angle_contract = packet.get(\"article_angle_contract\") or {}\n    if packet.get(\"article_angle_contract_version\"):\n        changes[\"article_angle_contract_version\"] = packet[\"article_angle_contract_version\"]\n        changes[\"information_gain_type\"] = angle_contract.get(\"angle_type\")\n        changes[\"angle_contract_verified\"] = True\n        changes[\"angle_approval_passed\"] = bool(article.get(\"angle_approval_passed\"))\n        changes[\"angle_delivery\"] = article.get(\"angle_delivery\") or {}\n    if primary_cluster:\n        changes[\"primary_seo_cluster_id\"] = primary_cluster\n",
)
replace_once(
    "engine/approval.py",
    "    quality_report = evaluate_quality(enriched)\n    editorial_report = evaluate_editorial(packet, article)\n",
    "    quality_report = evaluate_quality(enriched)\n    editorial_report = evaluate_editorial(packet, article)\n    angle_report = evaluate_article_angle(packet, article)\n    if angle_report.contracted:\n        enriched[\"article_angle_contract_version\"] = packet.get(\"article_angle_contract_version\")\n        enriched[\"information_gain_type\"] = (packet.get(\"article_angle_contract\") or {}).get(\"angle_type\")\n        enriched[\"angle_contract_verified\"] = True\n        enriched[\"angle_approval_passed\"] = angle_report.passed\n        enriched[\"angle_delivery\"] = article.get(\"angle_delivery\") or {}\n",
)
replace_once(
    "engine/approval.py",
    "        *editorial_report.errors, *seo_errors,\n",
    "        *editorial_report.errors, *angle_report.errors, *seo_errors,\n",
)
replace_once(
    "engine/approval.py",
    "        *editorial_report.warnings, *seo_warnings,\n",
    "        *editorial_report.warnings, *angle_report.warnings, *seo_warnings,\n",
)
replace_once(
    "engine/approval.py",
    "        and editorial_report.passed\n    )\n",
    "        and editorial_report.passed\n        and angle_report.passed\n    )\n",
)
replace_once(
    "engine/approval.py",
    "        editorial_score=editorial_report.score,\n",
    "        editorial_score=editorial_report.score,\n        angle_score=angle_report.score if angle_report.contracted else None,\n",
)
replace_once(
    "engine/approval.py",
    "    if article_id:\n        result.registry_record = append_article_state(article_id, result.status, _registry_changes(packet, article))\n",
    "    if article_id:\n        record_article = _enrich_for_quality(packet, article)\n        if result.registry_record:\n            for field in (\n                \"article_angle_contract_version\", \"information_gain_type\", \"angle_signature\",\n                \"angle_contract_verified\", \"angle_approval_passed\", \"angle_delivery\",\n            ):\n                if field in result.registry_record:\n                    record_article[field] = result.registry_record[field]\n        result.registry_record = append_article_state(article_id, result.status, _registry_changes(packet, record_article))\n",
)

# production_controller.py — expand deterministic angle variants only after the
# machine filter contract exists; apply real Registry gates to each variant; then
# preselect an internally conflict-free candidate pool using the unchanged 0.72 /
# 0.82 thresholds.
replace_once(
    "engine/production_controller.py",
    "from .ai_generation_v22 import generate_multistage_article\n",
    "from .ai_generation_v22 import generate_multistage_article\nfrom .article_angles import audited_angle_type, expand_article_angle_variants\n",
)
replace_once(
    "engine/production_controller.py",
    "from .dedup import duplicate_candidates\n",
    "from .dedup import LEXICAL_DUPLICATE_THRESHOLD, duplicate_candidates, lexical_similarity\n",
)
replace_once(
    "engine/production_controller.py",
    "from .semantic_dedup import structural_duplicate_candidates\nfrom .seo_keywords import normalize_keyword\n",
    "from .semantic_dedup import (\n    STRUCTURAL_DUPLICATE_THRESHOLD, structural_duplicate_candidates, structural_similarity,\n)\nfrom .seo_keywords import keyword_owners, normalize_keyword\n",
)
replace_once(
    "engine/production_controller.py",
    "        str(record.get(\"case_structure\") or \"\"),\n    )\n",
    "        str(record.get(\"case_structure\") or \"\"),\n        audited_angle_type(record) or \"\",\n    )\n",
)
replace_once(
    "engine/production_controller.py",
    "        result = plan_articles(provider_id, unit[\"lottery\"], unit[\"play\"], probe)\n",
    "        result = plan_articles(\n            provider_id, unit[\"lottery\"], unit[\"play\"], probe, include_used_angles=True\n        )\n",
)
replace_once(
    "engine/production_controller.py",
    "            blueprint = blueprint_from_plan(enriched_plan)\n",
    "            blueprint = blueprint_from_plan(enriched_plan, apply_registry_gates=False)\n",
)
old_loop = '''            _assign_cluster_metadata(blueprint, policy)\n            if blueprint.get("status") != "ready_for_draft":\n                continue\n            if blueprint.get("article_id") in existing_ids:\n                continue\n            keyword = normalize_keyword(blueprint.get("primary_keyword"))\n            if keyword and keyword in existing_keywords:\n                continue\n            if _structural_key(blueprint) in existing_structures:\n                continue\n            try:\n                contract = _bind_primary_filter_contract(blueprint)\n            except ProductionFilterContractError:\n                contract_blocked_here += 1\n                continue\n            mode = str(contract.get("mode") or "unknown")\n            contract_modes[mode] += 1\n            mode_here[mode] += 1\n            score_row = rank_blueprints([blueprint], signals)[0]\n            if not score_row.get("eligible"):\n                continue\n            raw_candidates.append({\n                "priority_score": float(score_row.get("priority_score") or 0),\n                "priority_band": score_row.get("priority_band"),\n                "blueprint": blueprint,\n            })\n            ready_here += 1\n'''
new_loop = '''            _assign_cluster_metadata(blueprint, policy)\n            if blueprint.get("status") != "ready_for_draft":\n                continue\n            try:\n                contract = _bind_primary_filter_contract(blueprint)\n            except ProductionFilterContractError:\n                contract_blocked_here += 1\n                continue\n            for variant in expand_article_angle_variants(blueprint):\n                article_id = str(variant.get("article_id") or "")\n                if not article_id or article_id in existing_ids:\n                    continue\n                keyword = normalize_keyword(variant.get("primary_keyword"))\n                if keyword and keyword in existing_keywords:\n                    continue\n                if keyword_owners(variant.get("primary_keyword"), exclude_article_id=article_id):\n                    continue\n                if _structural_key(variant) in existing_structures:\n                    continue\n                if duplicate_candidates(variant) or structural_duplicate_candidates(variant):\n                    continue\n                mode = str(contract.get("mode") or "unknown")\n                contract_modes[mode] += 1\n                mode_here[mode] += 1\n                score_row = rank_blueprints([variant], signals)[0]\n                if not score_row.get("eligible"):\n                    continue\n                raw_candidates.append({\n                    "priority_score": float(score_row.get("priority_score") or 0),\n                    "priority_band": score_row.get("priority_band"),\n                    "blueprint": variant,\n                })\n                ready_here += 1\n'''
replace_once("engine/production_controller.py", old_loop, new_loop)
replace_once(
    "engine/production_controller.py",
    "    final_modes = Counter()\n    for row in raw_candidates:\n",
    "    final_modes = Counter()\n    pool_duplicate_blocked = Counter()\n    for row in raw_candidates:\n",
)
replace_once(
    "engine/production_controller.py",
    "        seen_ids.add(article_id)\n",
    '''        pool_conflict = None\n        for chosen in candidates:\n            old = chosen["blueprint"]\n            lexical_score = lexical_similarity(blueprint, old)\n            if lexical_score >= LEXICAL_DUPLICATE_THRESHOLD:\n                pool_conflict = "lexical"\n                break\n            structural_score, _ = structural_similarity(blueprint, old)\n            if structural_score >= STRUCTURAL_DUPLICATE_THRESHOLD:\n                pool_conflict = "structural"\n                break\n        if pool_conflict:\n            pool_duplicate_blocked[pool_conflict] += 1\n            continue\n        seen_ids.add(article_id)\n''',
)
replace_once(
    "engine/production_controller.py",
    "        \"contract_mode_distribution\": dict(final_modes),\n        \"candidates\": candidates,\n",
    "        \"contract_mode_distribution\": dict(final_modes),\n        \"pool_duplicate_blocked\": sum(pool_duplicate_blocked.values()),\n        \"pool_duplicate_gate_distribution\": dict(pool_duplicate_blocked),\n        \"candidates\": candidates,\n",
)
replace_once(
    "engine/production_controller.py",
    "        \"contract_mode_distribution\": dict(portfolio.get(\"contract_mode_distribution\") or {}),\n",
    "        \"contract_mode_distribution\": dict(portfolio.get(\"contract_mode_distribution\") or {}),\n        \"pool_duplicate_blocked\": int(portfolio.get(\"pool_duplicate_blocked\") or 0),\n        \"pool_duplicate_gate_distribution\": dict(portfolio.get(\"pool_duplicate_gate_distribution\") or {}),\n",
)
replace_once(
    "engine/production_controller.py",
    "                    \"multistage_score\": multistage_score,\n                    \"errors\": approval.errors,\n",
    "                    \"multistage_score\": multistage_score,\n                    \"angle_score\": getattr(approval, \"angle_score\", None),\n                    \"errors\": approval.errors,\n",
)
replace_once(
    "engine/production_controller.py",
    "                \"multistage_score\": multistage_score,\n                \"provider_response_id\": response_id or None,\n",
    "                \"multistage_score\": multistage_score,\n                \"angle_score\": getattr(approval, \"angle_score\", None),\n                \"provider_response_id\": response_id or None,\n",
)
replace_once(
    "engine/production_controller.py",
    "                \"primary_seo_cluster_id\": package.get(\"primary_seo_cluster_id\"),\n",
    "                \"primary_seo_cluster_id\": package.get(\"primary_seo_cluster_id\"),\n                \"information_gain_type\": package.get(\"information_gain_type\"),\n",
)
replace_once(
    "engine/production_controller.py",
    "    multistage_scores = [int(row[\"multistage_score\"]) for row in successful_rows if row.get(\"multistage_score\") is not None]\n",
    "    multistage_scores = [int(row[\"multistage_score\"]) for row in successful_rows if row.get(\"multistage_score\") is not None]\n    angle_scores = [int(row[\"angle_score\"]) for row in successful_rows if row.get(\"angle_score\") is not None]\n    angle_distribution = Counter(str(row.get(\"information_gain_type\") or \"legacy\") for row in successful_rows)\n",
)
replace_once(
    "engine/production_controller.py",
    "        \"multistage_score_average\": round(sum(multistage_scores) / len(multistage_scores), 2) if multistage_scores else None,\n",
    "        \"multistage_score_average\": round(sum(multistage_scores) / len(multistage_scores), 2) if multistage_scores else None,\n        \"angle_score_average\": round(sum(angle_scores) / len(angle_scores), 2) if angle_scores else None,\n        \"article_angle_distribution\": dict(angle_distribution),\n",
)

print("audited article angle patch applied")
