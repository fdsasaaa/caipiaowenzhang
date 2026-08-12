from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import engine.group_mode_binding as group_binding
from engine.group_mode_binding import SOURCE_BINDING, bind_group_mode
from engine.source_materialization import (
    build_materialized_source_record,
    exact_term_index,
    materialize_source_file,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def _source_row(content: str, *, thread_id: int = 4115, title: str = "时时彩平台组六与胆码原文示例") -> dict:
    return {
        "source_name": "BRBCW",
        "thread_id": thread_id,
        "title": title,
        "url": f"https://example.invalid/thread-{thread_id}",
        "classification": "三星",
        "content": content,
    }


def test_materialized_record_preserves_raw_legacy_term_and_exact_content_hash():
    content = "原文写的是：时时彩后三组六，胆码另文说明。这里不做读者改写。"
    record = build_materialized_source_record(_source_row(content))

    assert record["source_id"] == "BRBCW-004115"
    assert record["content"] == content
    assert record["content_sha256"] == hashlib.sha256(content.encode("utf-8")).hexdigest()
    assert record["raw_source_policy"]["raw_source_text_mutated"] is False
    assert record["raw_source_policy"]["reader_display_preference"] == "分分彩"
    assert record["exact_term_index"]["legacy_ssc_term_count"] >= 1
    assert record["exact_term_index"]["ffc_term_count"] == 0
    assert any(row["term"] == "组六" for row in record["exact_term_index"]["group6_terms"])
    assert any(row["term"] == "胆码" for row in record["exact_term_index"]["dan_terms"])


def test_exact_term_index_records_literals_but_does_not_infer_dan_digits():
    index = exact_term_index("组三和胆码", "原文只说胆码，没有给出具体数字。")
    assert any(row["term"] == "组三" for row in index["group3_terms"])
    assert index["dan_terms"]
    assert "candidate_digit_set" not in index


def test_dry_run_does_not_write_source_snapshots(tmp_path: Path):
    input_path = tmp_path / "sources.jsonl"
    _write_jsonl(input_path, [_source_row("时时彩后三组六原文。")])
    output_dir = tmp_path / "knowledge" / "source_articles"
    manifest = tmp_path / "knowledge" / "source_manifests" / "materialized_sources.jsonl"

    result = materialize_source_file(
        input_path,
        root=tmp_path,
        output_dir=output_dir,
        manifest_path=manifest,
        apply=False,
    )
    assert result.ok is True
    assert result.materialized == 1
    assert not output_dir.exists()
    assert not manifest.exists()


def test_apply_writes_exact_snapshot_and_manifest_without_reader_rewrite(tmp_path: Path):
    content = " 时时彩 后三组六：三个数字互不相同。未来读者文章可改写成分分彩，但此处原文不改。 "
    input_path = tmp_path / "sources.jsonl"
    _write_jsonl(input_path, [_source_row(content)])
    output_dir = tmp_path / "knowledge" / "source_articles"
    manifest = tmp_path / "knowledge" / "source_manifests" / "materialized_sources.jsonl"

    result = materialize_source_file(
        input_path,
        root=tmp_path,
        output_dir=output_dir,
        manifest_path=manifest,
        apply=True,
    )
    assert result.ok is True
    record = json.loads((output_dir / "BRBCW-004115.json").read_text(encoding="utf-8"))
    assert record["content"] == content
    assert "时时彩" in record["content"]
    assert record["raw_source_policy"]["raw_source_text_mutated"] is False

    manifest_row = json.loads(manifest.read_text(encoding="utf-8").strip())
    assert manifest_row["source_id"] == "BRBCW-004115"
    assert manifest_row["content_sha256"] == record["content_sha256"]
    assert manifest_row["raw_source_text_mutated"] is False


def test_same_snapshot_is_idempotent_but_changed_content_conflicts(tmp_path: Path):
    input_path = tmp_path / "sources.jsonl"
    output_dir = tmp_path / "knowledge" / "source_articles"
    manifest = tmp_path / "knowledge" / "source_manifests" / "materialized_sources.jsonl"

    _write_jsonl(input_path, [_source_row("时时彩后三组六原始版本。")])
    first = materialize_source_file(input_path, root=tmp_path, output_dir=output_dir, manifest_path=manifest, apply=True)
    assert first.materialized == 1

    second = materialize_source_file(input_path, root=tmp_path, output_dir=output_dir, manifest_path=manifest, apply=True)
    assert second.unchanged == 1
    assert second.conflicts == 0

    _write_jsonl(input_path, [_source_row("同一个source id但正文已经变化。")])
    third = materialize_source_file(input_path, root=tmp_path, output_dir=output_dir, manifest_path=manifest, apply=True)
    assert third.ok is False
    assert third.conflicts == 1
    persisted = json.loads((output_dir / "BRBCW-004115.json").read_text(encoding="utf-8"))
    assert persisted["content"] == "时时彩后三组六原始版本。"


def test_materialized_exact_source_can_unlock_source_owned_group_mode_when_phrase_exists(tmp_path: Path, monkeypatch):
    input_path = tmp_path / "sources.jsonl"
    output_dir = tmp_path / "knowledge" / "source_articles"
    manifest = tmp_path / "knowledge" / "source_manifests" / "materialized_sources.jsonl"
    _write_jsonl(input_path, [_source_row("这篇原文明确讨论后三组六的结构与方法。")])
    result = materialize_source_file(input_path, root=tmp_path, output_dir=output_dir, manifest_path=manifest, apply=True)
    assert result.ok is True

    monkeypatch.setattr(group_binding, "SOURCE_ARTICLES", output_dir)
    binding = bind_group_mode(
        "FAM-f8efc151837be787",
        group_mode="group6",
        binding_basis=SOURCE_BINDING,
        source_ref="BRBCW-004115",
    )
    assert binding["mode_provenance"]["owner"] == "source"
    assert "组六" in binding["mode_provenance"]["matched_terms"]
    assert binding["source_did_not_choose_mode"] is False


def test_materialized_source_without_exact_group_phrase_cannot_unlock_source_mode(tmp_path: Path, monkeypatch):
    input_path = tmp_path / "sources.jsonl"
    output_dir = tmp_path / "knowledge" / "source_articles"
    manifest = tmp_path / "knowledge" / "source_manifests" / "materialized_sources.jsonl"
    _write_jsonl(input_path, [_source_row("这里只说组选方法，没有明确写组三或组六。")])
    materialize_source_file(input_path, root=tmp_path, output_dir=output_dir, manifest_path=manifest, apply=True)

    monkeypatch.setattr(group_binding, "SOURCE_ARTICLES", output_dir)
    with pytest.raises(Exception, match="does not explicitly contain"):
        bind_group_mode(
            "FAM-f8efc151837be787",
            group_mode="group6",
            binding_basis=SOURCE_BINDING,
            source_ref="BRBCW-004115",
        )


def test_title_only_group_phrase_is_indexable_but_cannot_transfer_source_mode_ownership(tmp_path: Path, monkeypatch):
    input_path = tmp_path / "sources.jsonl"
    output_dir = tmp_path / "knowledge" / "source_articles"
    manifest = tmp_path / "knowledge" / "source_manifests" / "materialized_sources.jsonl"
    _write_jsonl(input_path, [_source_row("正文只讨论广义组选方法，没有指定具体模式。")])
    materialize_source_file(input_path, root=tmp_path, output_dir=output_dir, manifest_path=manifest, apply=True)

    record = json.loads((output_dir / "BRBCW-004115.json").read_text(encoding="utf-8"))
    assert record["exact_term_index"]["group6_terms"]  # title remains searchable/indexable

    monkeypatch.setattr(group_binding, "SOURCE_ARTICLES", output_dir)
    with pytest.raises(Exception, match="article body does not explicitly contain"):
        bind_group_mode(
            "FAM-f8efc151837be787",
            group_mode="group6",
            binding_basis=SOURCE_BINDING,
            source_ref="BRBCW-004115",
        )


def test_negated_group_phrase_in_body_cannot_transfer_source_mode_ownership(tmp_path: Path, monkeypatch):
    input_path = tmp_path / "sources.jsonl"
    output_dir = tmp_path / "knowledge" / "source_articles"
    manifest = tmp_path / "knowledge" / "source_manifests" / "materialized_sources.jsonl"
    _write_jsonl(
        input_path,
        [_source_row("本文不是组六方法，只讨论一般组选结构。", title="组选方法说明")],
    )
    materialize_source_file(input_path, root=tmp_path, output_dir=output_dir, manifest_path=manifest, apply=True)

    monkeypatch.setattr(group_binding, "SOURCE_ARTICLES", output_dir)
    with pytest.raises(Exception, match="does not explicitly contain"):
        bind_group_mode(
            "FAM-f8efc151837be787",
            group_mode="group6",
            binding_basis=SOURCE_BINDING,
            source_ref="BRBCW-004115",
        )
