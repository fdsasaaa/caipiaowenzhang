from pathlib import Path

pc = Path('engine/production_controller.py')
text = pc.read_text(encoding='utf-8')
text = text.replace(
    'from .draft_packets import build_case_bundle, build_draft_packet\n',
    'from .dedup import duplicate_candidates\nfrom .draft_packets import build_case_bundle, build_draft_packet\n'
)
text = text.replace(
    'from .rules import load_rules\n',
    'from .rules import load_rules\nfrom .semantic_dedup import structural_duplicate_candidates\n'
)
marker = '''def _default_generator_for_packet(packet: dict) -> Callable:\n    if packet.get("contract_version") == "2.2-multistage":\n        return generate_multistage_article\n    return generate_article\n\n\n'''
helper = '''def _default_generator_for_packet(packet: dict) -> Callable:\n    if packet.get("contract_version") == "2.2-multistage":\n        return generate_multistage_article\n    return generate_article\n\n\ndef _pre_generation_duplicate_block(blueprint: dict) -> dict | None:\n    \"\"\"Use the same live Registry duplicate gates before any provider request.\n\n    The Registry is re-read for every candidate, so a newly approved/staged article\n    immediately becomes a dedup owner for the next candidate in the same run.\n    Rejected/revision-only lifecycle rows remain non-owning through the underlying\n    duplicate helpers.\n    \"\"\"\n    lexical = duplicate_candidates(blueprint)\n    if lexical:\n        hit = lexical[0]\n        return {\n            "duplicate_gate": "lexical",\n            "duplicate_article_id": hit.article_id,\n            "duplicate_score": round(float(hit.score), 4),\n            "duplicate_reason": hit.reason,\n        }\n    structural = structural_duplicate_candidates(blueprint)\n    if structural:\n        hit = structural[0]\n        return {\n            "duplicate_gate": "structural",\n            "duplicate_article_id": hit.article_id,\n            "duplicate_score": round(float(hit.score), 4),\n            "duplicate_reason": ",".join(hit.reasons),\n        }\n    return None\n\n\n'''
assert marker in text, 'default generator marker missing'
text = text.replace(marker, helper, 1)

text = text.replace(
    '    terminology_failed = 0\n',
    '    terminology_failed = 0\n    pre_generation_duplicate_blocked = 0\n'
)
old = '''            blueprint = candidate["blueprint"]\n            article_id = str(blueprint.get("article_id") or "")\n            attempted += 1\n            packet = _packet_with_cluster_metadata(blueprint)\n'''
new = '''            blueprint = candidate["blueprint"]\n            article_id = str(blueprint.get("article_id") or "")\n            duplicate_block = _pre_generation_duplicate_block(blueprint)\n            if duplicate_block:\n                pre_generation_duplicate_blocked += 1\n                rows.append({\n                    "article_id": article_id,\n                    "status": "pre_generation_duplicate_blocked",\n                    "approved": False,\n                    **duplicate_block,\n                })\n                continue\n            attempted += 1\n            packet = _packet_with_cluster_metadata(blueprint)\n'''
assert old in text, 'provider-attempt marker missing'
text = text.replace(old, new, 1)

old = '''            generated += 1\n            article = normalize_generation_metadata(generation.article)\n            multistage_score = None\n'''
new = '''            generated += 1\n            response_id = str(getattr(generation, "response_id", "") or "")\n            article = normalize_generation_metadata(generation.article)\n            if response_id:\n                article["provider_response_id"] = response_id\n            multistage_score = None\n'''
assert old in text, 'generation metadata marker missing'
text = text.replace(old, new, 1)

text = text.replace(
    '                        "multistage_score": multistage.score,\n                        "errors": errors,\n',
    '                        "multistage_score": multistage.score,\n                        "provider_response_id": response_id or None,\n                        "errors": errors,\n',
    1
)
text = text.replace(
    '                    "multistage_score": multistage_score,\n                    "errors": approval.errors,\n',
    '                    "multistage_score": multistage_score,\n                    "provider_response_id": response_id or None,\n                    "errors": approval.errors,\n',
    1
)
text = text.replace(
    '                    "multistage_score": multistage_score,\n                    "errors": terminology_errors,\n',
    '                    "multistage_score": multistage_score,\n                    "provider_response_id": response_id or None,\n                    "errors": terminology_errors,\n',
    1
)
text = text.replace(
    '                "multistage_score": multistage_score,\n                "primary_keyword": package.get("primary_keyword"),\n',
    '                "multistage_score": multistage_score,\n                "provider_response_id": response_id or None,\n                "primary_keyword": package.get("primary_keyword"),\n',
    1
)
text = text.replace(
    '        "approval_failed": approval_failed,\n        "multistage_failed": multistage_failed,\n',
    '        "approval_failed": approval_failed,\n        "pre_generation_duplicate_blocked": pre_generation_duplicate_blocked,\n        "multistage_failed": multistage_failed,\n',
    1
)
text = text.replace(
    '        "published": False,\n        "results": rows,\n',
    '        "published": False,\n        "provider_response_ids": [row["provider_response_id"] for row in rows if row.get("provider_response_id")],\n        "results": rows,\n',
    1
)
pc.write_text(text, encoding='utf-8')

ap = Path('engine/approval.py')
text = ap.read_text(encoding='utf-8')
text = text.replace(
    '        "provider_id": facts.get("provider_id") or existing.get("provider_id"),\n',
    '        "provider_id": facts.get("provider_id") or existing.get("provider_id"),\n        "provider_response_id": article.get("provider_response_id") or existing.get("provider_response_id"),\n',
    1
)
marker = '''        "content_hash": sha256_text(article.get("content", "")) if article.get("content") else None,\n    }\n'''
replacement = '''        "content_hash": sha256_text(article.get("content", "")) if article.get("content") else None,\n        "provider_response_id": article.get("provider_response_id") or existing.get("provider_response_id"),\n    }\n'''
assert marker in text, 'registry changes marker missing'
text = text.replace(marker, replacement, 1)
ap.write_text(text, encoding='utf-8')

tests = Path('tests/test_production_controller.py')
t = tests.read_text(encoding='utf-8')
assert 'test_controller_blocks_live_duplicate_before_provider' not in t

t += r'''


def test_controller_blocks_live_duplicate_before_provider(monkeypatch):
    calls = {"generate": 0}

    def fake_generate(packet, **kwargs):
        calls["generate"] += 1
        return SimpleNamespace(article={"article_id": packet["article_id"]}, response_id="resp-never")

    monkeypatch.setattr(
        "engine.production_controller.duplicate_candidates",
        lambda blueprint: [SimpleNamespace(article_id="LIVE-001", score=0.84, reason="lexical/core overlap")],
    )
    monkeypatch.setattr("engine.production_controller.structural_duplicate_candidates", lambda blueprint: [])
    plan = {
        "target_new_formal_articles": 1,
        "batch_size": 1,
        "candidates": [{"priority_score": 90, "blueprint": _blueprint("CTRL-DUP-001")}],
    }
    result = execute_production_plan(plan, generate_fn=fake_generate)
    assert calls["generate"] == 0
    assert result["attempted"] == 0
    assert result["generated"] == 0
    assert result["pre_generation_duplicate_blocked"] == 1
    assert result["results"][0]["status"] == "pre_generation_duplicate_blocked"
    assert result["results"][0]["duplicate_article_id"] == "LIVE-001"


def test_controller_rechecks_registry_before_each_candidate(monkeypatch):
    duplicate_checks = {"count": 0}
    generation_calls = {"count": 0}

    def fake_duplicate(blueprint):
        duplicate_checks["count"] += 1
        if duplicate_checks["count"] == 1:
            return []
        return [SimpleNamespace(article_id="CTRL-FIRST", score=0.81, reason="lexical/core overlap")]

    def fake_generate(packet, **kwargs):
        generation_calls["count"] += 1
        return SimpleNamespace(article={"article_id": packet["article_id"]}, response_id=f"resp-{generation_calls['count']}")

    def fake_approve(packet, article):
        package = _package(article["article_id"])
        package["provider_response_id"] = article.get("provider_response_id")
        return SimpleNamespace(approved=True, publish_package=package, status="approved", quality_score=100, editorial_score=100, errors=[])

    def fake_stage(package):
        return {"status": "staged", "article_id": package["article_id"]}

    monkeypatch.setattr("engine.production_controller.duplicate_candidates", fake_duplicate)
    monkeypatch.setattr("engine.production_controller.structural_duplicate_candidates", lambda blueprint: [])
    plan = {
        "target_new_formal_articles": 2,
        "batch_size": 2,
        "candidates": [
            {"priority_score": 100, "blueprint": _blueprint("CTRL-FIRST")},
            {"priority_score": 90, "blueprint": _blueprint("CTRL-SECOND")},
        ],
    }
    result = execute_production_plan(plan, generate_fn=fake_generate, approve_fn=fake_approve, stage_fn=fake_stage)
    assert duplicate_checks["count"] == 2
    assert generation_calls["count"] == 1
    assert result["attempted"] == 1
    assert result["formal_inventory_staged"] == 1
    assert result["pre_generation_duplicate_blocked"] == 1


def test_controller_records_provider_response_id(monkeypatch):
    monkeypatch.setattr("engine.production_controller.duplicate_candidates", lambda blueprint: [])
    monkeypatch.setattr("engine.production_controller.structural_duplicate_candidates", lambda blueprint: [])
    seen = {}

    def fake_generate(packet, **kwargs):
        return SimpleNamespace(article={"article_id": packet["article_id"]}, response_id="resp-controller-audit-001")

    def fake_approve(packet, article):
        seen["article_response_id"] = article.get("provider_response_id")
        package = _package(article["article_id"])
        package["provider_response_id"] = article.get("provider_response_id")
        return SimpleNamespace(approved=True, publish_package=package, status="approved", quality_score=100, editorial_score=100, errors=[])

    def fake_stage(package):
        seen["package_response_id"] = package.get("provider_response_id")
        return {"status": "staged", "article_id": package["article_id"]}

    plan = {
        "target_new_formal_articles": 1,
        "batch_size": 1,
        "candidates": [{"priority_score": 100, "blueprint": _blueprint("CTRL-AUDIT-001")}],
    }
    result = execute_production_plan(plan, generate_fn=fake_generate, approve_fn=fake_approve, stage_fn=fake_stage)
    assert seen["article_response_id"] == "resp-controller-audit-001"
    assert seen["package_response_id"] == "resp-controller-audit-001"
    assert result["provider_response_ids"] == ["resp-controller-audit-001"]
    assert result["results"][0]["provider_response_id"] == "resp-controller-audit-001"
'''

tests.write_text(t, encoding='utf-8')
