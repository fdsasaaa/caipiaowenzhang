from __future__ import annotations

import hashlib

POSITION_MAP = {
    "后三": ["百位", "十位", "个位"],
    "前三": ["万位", "千位", "百位"],
    "中三": ["千位", "百位", "十位"],
    "后二": ["十位", "个位"],
    "前二": ["万位", "千位"],
}

OP_METRIC = {
    "sum_range": "sum_range",
    "span_range": "span_range",
    "odd_count": "odd_count",
    "big_count": "big_count",
    "distinct_count": "distinct_count",
    "digit_pool": "digit_pool",
    "pair_sum_range": "pair_sum",
    "mixed_parity": "mixed_parity",
}


def _stage(stage_id: str, label: str, atom: str, op: str, params: dict) -> dict:
    return {
        "id": stage_id,
        "label": label,
        "atom": atom,
        "op": op,
        "params": params,
        "basis": "experimental_parameter",
    }


CASES = [
    {
        "id": "011", "play": "后三直选", "selector": "后三",
        "title": "分分彩后三直选和值奇偶技巧：和值7–15后筛恰好2个奇数",
        "primary": "分分彩后三直选和值奇偶技巧",
        "stages": [
            _stage("sum_7_15", "和值7–15", "sum_range", "sum_range", {"min": 7, "max": 15}),
            _stage("odd_2", "恰好2个奇数", "odd_even_filter", "odd_count", {"count": 2}),
        ],
        "rule": "SSC-HIST-MECH-3STAR-LAST-V1", "expected": [1000, 564, 186],
    },
    {
        "id": "012", "play": "后三直选", "selector": "后三",
        "title": "分分彩后三直选跨度大小技巧：跨度3–7后筛恰好1个大号",
        "primary": "分分彩后三直选跨度大小技巧",
        "stages": [
            _stage("span_3_7", "跨度3–7", "span_range", "span_range", {"min": 3, "max": 7}),
            _stage("big_1", "恰好1个大号", "big_small_filter", "big_count", {"count": 1}),
        ],
        "rule": "SSC-HIST-MECH-3STAR-LAST-V1", "expected": [1000, 690, 285],
    },
    {
        "id": "013", "play": "后三直选", "selector": "后三",
        "title": "分分彩后三直选六码池全异技巧：固定0/2/3/5/7/9后排除重复",
        "primary": "分分彩后三直选六码池全异技巧",
        "stages": [
            _stage("pool_023579", "候选数字池0/2/3/5/7/9", "compound_selection", "digit_pool", {"digits": [0, 2, 3, 5, 7, 9]}),
            _stage("distinct_3", "三位全异", "repeat_number", "distinct_count", {"count": 3}),
        ],
        "rule": "SSC-HIST-MECH-3STAR-LAST-V1", "expected": [1000, 216, 120],
    },
    {
        "id": "014", "play": "后三直选", "selector": "后三",
        "title": "分分彩后三直选奇偶跨度和值技巧：1个奇数→跨度2–6→和值8–18",
        "primary": "分分彩后三直选奇偶跨度和值技巧",
        "stages": [
            _stage("odd_1", "恰好1个奇数", "odd_even_filter", "odd_count", {"count": 1}),
            _stage("span_2_6", "跨度2–6", "span_range", "span_range", {"min": 2, "max": 6}),
            _stage("sum_8_18", "和值8–18", "sum_range", "sum_range", {"min": 8, "max": 18}),
        ],
        "rule": "SSC-HIST-MECH-3STAR-LAST-V1", "expected": [1000, 375, 234, 141],
    },
    {
        "id": "015", "play": "前三直选", "selector": "前三",
        "title": "分分彩前三直选大小全异技巧：2个大号后只留三位全异",
        "primary": "分分彩前三直选大小全异技巧",
        "stages": [
            _stage("big_2", "恰好2个大号", "big_small_filter", "big_count", {"count": 2}),
            _stage("distinct_3", "三位全异", "repeat_number", "distinct_count", {"count": 3}),
        ],
        "rule": "SSC-DERIVED-MECH-FRONT3-DIRECT-V1", "expected": [1000, 375, 300],
    },
    {
        "id": "016", "play": "前三直选", "selector": "前三",
        "title": "分分彩前三直选七码池和值技巧：0/1/3/4/7/8/9后筛和值10–20",
        "primary": "分分彩前三直选七码池和值技巧",
        "stages": [
            _stage("pool_0134789", "候选数字池0/1/3/4/7/8/9", "compound_selection", "digit_pool", {"digits": [0, 1, 3, 4, 7, 8, 9]}),
            _stage("sum_10_20", "和值10–20", "sum_range", "sum_range", {"min": 10, "max": 20}),
        ],
        "rule": "SSC-DERIVED-MECH-FRONT3-DIRECT-V1", "expected": [1000, 343, 223],
    },
    {
        "id": "017", "play": "前三直选", "selector": "前三",
        "title": "分分彩前三直选和值大小重号技巧：和值6–16→1个大号→两位不同",
        "primary": "分分彩前三直选和值大小重号技巧",
        "stages": [
            _stage("sum_6_16", "和值6–16", "sum_range", "sum_range", {"min": 6, "max": 16}),
            _stage("big_1", "恰好1个大号", "big_small_filter", "big_count", {"count": 1}),
            _stage("distinct_2", "恰好2个不同数字", "repeat_number", "distinct_count", {"count": 2}),
        ],
        "rule": "SSC-DERIVED-MECH-FRONT3-DIRECT-V1", "expected": [1000, 661, 369, 69],
    },
    {
        "id": "018", "play": "前三直选", "selector": "前三",
        "title": "分分彩前三直选跨度奇偶技巧：跨度2–5后筛恰好2个奇数",
        "primary": "分分彩前三直选跨度奇偶技巧",
        "stages": [
            _stage("span_2_5", "跨度2–5", "span_range", "span_range", {"min": 2, "max": 5}),
            _stage("odd_2", "恰好2个奇数", "odd_even_filter", "odd_count", {"count": 2}),
        ],
        "rule": "SSC-DERIVED-MECH-FRONT3-DIRECT-V1", "expected": [1000, 516, 198],
    },
    {
        "id": "019", "play": "中三直选", "selector": "中三",
        "title": "分分彩中三直选和值全异技巧：和值11–21后排除重复号码",
        "primary": "分分彩中三直选和值全异技巧",
        "stages": [
            _stage("sum_11_21", "和值11–21", "sum_range", "sum_range", {"min": 11, "max": 21}),
            _stage("distinct_3", "三位全异", "repeat_number", "distinct_count", {"count": 3}),
        ],
        "rule": "SSC-DERIVED-MECH-MIDDLE3-DIRECT-V1", "expected": [1000, 661, 510],
    },
    {
        "id": "020", "play": "中三直选", "selector": "中三",
        "title": "分分彩中三直选六码池大小技巧：1/2/4/5/6/8后筛2个大号",
        "primary": "分分彩中三直选六码池大小技巧",
        "stages": [
            _stage("pool_124568", "候选数字池1/2/4/5/6/8", "compound_selection", "digit_pool", {"digits": [1, 2, 4, 5, 6, 8]}),
            _stage("big_2", "恰好2个大号", "big_small_filter", "big_count", {"count": 2}),
        ],
        "rule": "SSC-DERIVED-MECH-MIDDLE3-DIRECT-V1", "expected": [1000, 216, 81],
    },
    {
        "id": "021", "play": "中三直选", "selector": "中三",
        "title": "分分彩中三直选大小跨度奇偶技巧：1个大号→跨度4–8→1个奇数",
        "primary": "分分彩中三直选大小跨度奇偶技巧",
        "stages": [
            _stage("big_1", "恰好1个大号", "big_small_filter", "big_count", {"count": 1}),
            _stage("span_4_8", "跨度4–8", "span_range", "span_range", {"min": 4, "max": 8}),
            _stage("odd_1", "恰好1个奇数", "odd_even_filter", "odd_count", {"count": 1}),
        ],
        "rule": "SSC-DERIVED-MECH-MIDDLE3-DIRECT-V1", "expected": [1000, 375, 306, 117],
    },
    {
        "id": "022", "play": "中三直选", "selector": "中三",
        "title": "分分彩中三直选奇偶和值技巧：2个奇数后筛和值9–17",
        "primary": "分分彩中三直选奇偶和值技巧",
        "stages": [
            _stage("odd_2", "恰好2个奇数", "odd_even_filter", "odd_count", {"count": 2}),
            _stage("sum_9_17", "和值9–17", "sum_range", "sum_range", {"min": 9, "max": 17}),
        ],
        "rule": "SSC-DERIVED-MECH-MIDDLE3-DIRECT-V1", "expected": [1000, 375, 210],
    },
    {
        "id": "023", "play": "后二组选", "selector": "后二",
        "title": "分分彩后二组选和值数字池技巧：对子和值5–13后再套七码池",
        "primary": "分分彩后二组选和值数字池技巧",
        "stages": [
            _stage("pair_sum_5_13", "对子和值5–13", "sum_range", "pair_sum_range", {"min": 5, "max": 13}),
            _stage("pool_0135689", "候选数字池0/1/3/5/6/8/9", "compound_selection", "digit_pool", {"digits": [0, 1, 3, 5, 6, 8, 9]}),
        ],
        "rule": "SSC-HIST-MECH-2STAR-GROUP-V1", "expected": [45, 33, 14],
    },
    {
        "id": "024", "play": "后二组选", "selector": "后二",
        "title": "分分彩后二组选奇偶数字池技巧：先留一奇一偶再套六码池",
        "primary": "分分彩后二组选奇偶数字池技巧",
        "stages": [
            _stage("mixed_parity", "一奇一偶", "odd_even_filter", "mixed_parity", {}),
            _stage("pool_023578", "候选数字池0/2/3/5/7/8", "compound_selection", "digit_pool", {"digits": [0, 2, 3, 5, 7, 8]}),
        ],
        "rule": "SSC-HIST-MECH-2STAR-GROUP-V1", "expected": [45, 25, 9],
    },
    {
        "id": "025", "play": "后二组选", "selector": "后二",
        "title": "分分彩后二组选和值奇偶数字池技巧：和值6–14→一奇一偶→七码池",
        "primary": "分分彩后二组选和值奇偶数字池技巧",
        "stages": [
            _stage("pair_sum_6_14", "对子和值6–14", "sum_range", "pair_sum_range", {"min": 6, "max": 14}),
            _stage("mixed_parity", "一奇一偶", "odd_even_filter", "mixed_parity", {}),
            _stage("pool_0145789", "候选数字池0/1/4/5/7/8/9", "compound_selection", "digit_pool", {"digits": [0, 1, 4, 5, 7, 8, 9]}),
        ],
        "rule": "SSC-HIST-MECH-2STAR-GROUP-V1", "expected": [45, 32, 16, 7],
    },
    {
        "id": "026", "play": "后二组选", "selector": "后二",
        "title": "分分彩后二组选数字池和值奇偶技巧：六码池→和值7–13→一奇一偶",
        "primary": "分分彩后二组选数字池和值奇偶技巧",
        "stages": [
            _stage("pool_023578", "候选数字池0/2/3/5/7/8", "compound_selection", "digit_pool", {"digits": [0, 2, 3, 5, 7, 8]}),
            _stage("pair_sum_7_13", "对子和值7–13", "sum_range", "pair_sum_range", {"min": 7, "max": 13}),
            _stage("mixed_parity", "一奇一偶", "odd_even_filter", "mixed_parity", {}),
        ],
        "rule": "SSC-HIST-MECH-2STAR-GROUP-V1", "expected": [45, 15, 10, 5],
    },
    {
        "id": "027", "play": "前二组选", "selector": "前二",
        "title": "分分彩前二组选和值数字池奇偶技巧：和值4–12→七码池→一奇一偶",
        "primary": "分分彩前二组选和值数字池奇偶技巧",
        "stages": [
            _stage("pair_sum_4_12", "对子和值4–12", "sum_range", "pair_sum_range", {"min": 4, "max": 12}),
            _stage("pool_0124679", "候选数字池0/1/2/4/6/7/9", "compound_selection", "digit_pool", {"digits": [0, 1, 2, 4, 6, 7, 9]}),
            _stage("mixed_parity", "一奇一偶", "odd_even_filter", "mixed_parity", {}),
        ],
        "rule": "SSC-DERIVED-MECH-FRONT2-GROUP-V1", "expected": [45, 32, 14, 7],
    },
    {
        "id": "028", "play": "前二组选", "selector": "前二",
        "title": "分分彩前二组选奇偶和值数字池技巧：一奇一偶→和值7–13→六码池",
        "primary": "分分彩前二组选奇偶和值数字池技巧",
        "stages": [
            _stage("mixed_parity", "一奇一偶", "odd_even_filter", "mixed_parity", {}),
            _stage("pair_sum_7_13", "对子和值7–13", "sum_range", "pair_sum_range", {"min": 7, "max": 13}),
            _stage("pool_023569", "候选数字池0/2/3/5/6/9", "compound_selection", "digit_pool", {"digits": [0, 2, 3, 5, 6, 9]}),
        ],
        "rule": "SSC-DERIVED-MECH-FRONT2-GROUP-V1", "expected": [45, 25, 16, 5],
    },
    {
        "id": "029", "play": "前二组选", "selector": "前二",
        "title": "分分彩前二组选数字池奇偶和值技巧：六码池→一奇一偶→和值6–12",
        "primary": "分分彩前二组选数字池奇偶和值技巧",
        "stages": [
            _stage("pool_012569", "候选数字池0/1/2/5/6/9", "compound_selection", "digit_pool", {"digits": [0, 1, 2, 5, 6, 9]}),
            _stage("mixed_parity", "一奇一偶", "odd_even_filter", "mixed_parity", {}),
            _stage("pair_sum_6_12", "对子和值6–12", "sum_range", "pair_sum_range", {"min": 6, "max": 12}),
        ],
        "rule": "SSC-DERIVED-MECH-FRONT2-GROUP-V1", "expected": [45, 15, 9, 5],
    },
    {
        "id": "030", "play": "前二组选", "selector": "前二",
        "title": "分分彩前二组选奇偶数字池和值技巧：一奇一偶→八码池→和值8–14",
        "primary": "分分彩前二组选奇偶数字池和值技巧",
        "stages": [
            _stage("mixed_parity", "一奇一偶", "odd_even_filter", "mixed_parity", {}),
            _stage("pool_12346789", "候选数字池1/2/3/4/6/7/8/9", "compound_selection", "digit_pool", {"digits": [1, 2, 3, 4, 6, 7, 8, 9]}),
            _stage("pair_sum_8_14", "对子和值8–14", "sum_range", "pair_sum_range", {"min": 8, "max": 14}),
        ],
        "rule": "SSC-DERIVED-MECH-FRONT2-GROUP-V1", "expected": [45, 25, 16, 8],
    },
]


def _fingerprint(case_id: str) -> str:
    return hashlib.sha256(f"v22-stability-20-new-{case_id}".encode("utf-8")).hexdigest()


def _secondary_keywords(case: dict) -> list[str]:
    selector = case["selector"]
    play = case["play"]
    return [
        f"分分彩{play}",
        f"{selector}多层筛选",
        f"{selector}候选空间",
        "分分彩投注技巧研究",
    ]


def build_stability_blueprint(case: dict) -> dict:
    selector = case["selector"]
    group_play = "组选" in case["play"]
    space_type = "unordered_2digit" if group_play else "ordered_3digit"
    starting_space = 45 if group_play else 1000
    subject_play = case["play"] + "复式" if group_play else case["play"]
    stages = [dict(stage) for stage in case["stages"]]
    stage_labels = [stage["label"] for stage in stages]
    atoms = [stage["atom"] for stage in stages]
    metrics = [OP_METRIC[stage["op"]] for stage in stages]
    outline = [f"{case['play']}的理论候选空间怎么确定"]
    outline.extend(
        f"第{index}层：{stage['label']}如何从上一层继续缩小候选"
        for index, stage in enumerate(stages, start=1)
    )
    outline.extend([
        "实际怎么操作：逐层记录before、after和excluded",
        "冻结参数只表示研究条件，不代表预测优势",
        "完成预冻结最后一层后停止临时加条件",
    ])
    return {
        "blueprint_id": f"BP-V22-STAB20-{case['id']}",
        "article_id": f"LCM-STAB20-V22-{case['id']}",
        "provider_id": None,
        "lottery": "时时彩",
        "play": case["play"],
        "subject_lottery": "分分彩",
        "subject_play": subject_play,
        "content_type": "technique_article",
        "site_category_key": "tzjq",
        "technique_family": f"V22-STAB20-{case['id']}",
        "technique_atoms": atoms,
        "resolved_selector": selector,
        "selector_basis": "verified_play",
        "source_positions": POSITION_MAP[selector],
        "angle_signature": f"v22-stability-20-new-{case['id']}",
        "title": case["title"],
        "slug_seed": f"v22-stability-20-{case['id']}",
        "primary_keyword": case["primary"],
        "secondary_keywords": _secondary_keywords(case),
        "search_intent": (
            f"看懂分分彩{case['play']}如何按预冻结顺序执行"
            + "、".join(stage_labels)
            + "并复算每层候选空间"
        ),
        "information_gain_type": "prefrozen_multistage_filter_case",
        "summary_goal": (
            f"从{starting_space}个理论候选开始，按"
            + " → ".join(stage_labels)
            + "逐层复算，不把空间收缩解释成预测优势。"
        ),
        "outline": outline,
        "case_structure": (
            f"selector={selector};metrics={','.join(metrics)};scope=mechanics_only"
        ),
        "case_plan": {
            "supported": [
                {"atom": stage["atom"], "metric": OP_METRIC[stage["op"]]}
                for stage in stages
            ],
            "unsupported": [],
            "case_engine_ready": True,
            "resolved_selector": selector,
            "selector_basis": "verified_play",
            "source_position_supported": True,
        },
        "filter_pipeline_spec": {
            "space_type": space_type,
            "starting_space": starting_space,
            "stages": stages,
        },
        "case_scope": "mechanics_only",
        "rule_refs": [case["rule"]],
        "source_refs": [],
        "source_support_count": 0,
        "source_risk_rate": 0.0,
        "fingerprint": _fingerprint(case["id"]),
        "status": "ready_for_draft",
        "blockers": [],
        "article_status": "idea",
        "editorial_contract_version": "1.1",
        "seo_requirements": {
            "plain_chinese": True,
            "example_required": True,
            "unique_information_gain_required": True,
            "unique_exact_primary_keyword_required": True,
            "avoid_keyword_stuffing": True,
            "avoid_guaranteed_outcomes": True,
        },
    }


def stability_suite_20() -> list[tuple[dict, list[int]]]:
    return [(build_stability_blueprint(case), list(case["expected"])) for case in CASES]
