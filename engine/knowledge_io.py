from __future__ import annotations

import base64
import bz2
import gzip
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVES = ROOT / "knowledge" / "archives"

BRBCW_ATOMS = ["big_small_filter", "carry_mapping", "cold_hot_split", "compound_selection", "consecutive_number", "dan_candidate", "exclude_after_event", "follow_after_event", "frequency_window", "group3_group6", "kill_candidate", "neighbor_number", "odd_even_filter", "omission_threshold", "position_filter", "progressive_staking", "recent_digit_exclusion", "repeat_number", "span_range", "stop_loss", "stop_win", "sum_range"]
BRBCW_POSITIONS = ["万位", "个位", "五星", "前三", "前二", "前四", "十位", "千位", "后三", "后二", "后四", "百位"]
BRBCW_LOTTERIES = ["11选5", "七星彩", "分分彩", "双色球", "快三", "排列三", "时时彩", "福彩3D"]
BRBCW_CLASSES = ["倍投资金", "冷热", "和值", "复式组合", "奇偶大小", "定位胆", "未分类", "杀号", "概率统计", "玩法教程", "组选", "胆码", "跨度", "遗漏", "重号连号"]
BRBCW_FAMILY_RECORD = struct.Struct(">IHHHHHI")


def iter_archive_jsonl(path: Path):
    if not path.exists():
        return
    encoded = path.read_text(encoding="ascii").strip()
    if not encoded:
        return
    raw = gzip.decompress(base64.b64decode(encoded))
    for line in raw.decode("utf-8").splitlines():
        if line.strip():
            yield json.loads(line)


def archive_path(name: str) -> Path:
    return ARCHIVES / f"{name}.jsonl.gz.b64"


def _decode_mask(mask: int, values: list[str]) -> list[str]:
    return [value for i, value in enumerate(values) if mask & (1 << i)]


def iter_brbcw_families():
    archive_dir = ROOT / "knowledge" / "family_archives"
    parts = sorted(archive_dir.glob("brbcw_families_v1.part-*.b64"))
    if not parts:
        return
    encoded = "".join(p.read_text(encoding="ascii").strip() for p in parts)
    raw = bz2.decompress(base64.b64decode(encoded))
    if len(raw) % BRBCW_FAMILY_RECORD.size:
        raise ValueError("Invalid brbcw compact family archive length")
    for offset in range(0, len(raw), BRBCW_FAMILY_RECORD.size):
        atom_mask, pos_mask, lottery_mask, class_mask, source_count, risk_bp, example_thread = BRBCW_FAMILY_RECORD.unpack_from(raw, offset)
        atoms = _decode_mask(atom_mask, BRBCW_ATOMS)
        family_id = "FAM-" + hashlib.sha1(",".join(atoms).encode("utf-8")).hexdigest()[:16]
        yield {
            "f": family_id,
            "n": source_count,
            "r": risk_bp / 10000.0,
            "a": atoms,
            "p": _decode_mask(pos_mask, BRBCW_POSITIONS),
            "l": _decode_mask(lottery_mask, BRBCW_LOTTERIES),
            "c": _decode_mask(class_mask, BRBCW_CLASSES),
            "e": [f"BRBCW-{example_thread:06d}"] if example_thread else [],
        }
