from __future__ import annotations

import hashlib

POSITION_MAP = {
    "后三": ["百位", "十位", "个位"],
    "前三": ["万位", "千位", "百位"],
    "中三": ["千位", "百位", "十位"],
    "后二": ["十位", "个位"],
    "前二": ["万位", "千位"],
}

CASES = [
    {
        "id": "001", "play": "后三直选", "selector": "后三",
        "family": "V22-STAB-BACK3-SUM-SPAN", "atoms": ["sum_range", "span_range"],
        "title": "分分彩后三直选和值跨度技巧：先筛和值9–18再筛跨度2–6",
        "primary": "分分彩后三直选和值跨度技巧",
        "secondary": ["分分彩后三直选", "后三和值技巧", "后三跨度技巧", "时时彩筛选"],
        "intent": "看懂分分彩后三直选如何按预冻结和值与跨度两层复算候选空间",
        "summary": "从1000个后三有序结果开始，先筛和值9–18，再筛跨度2–6，展示1000→670→396。",
        "metrics": ["sum_range", "span_range"],
        "outline": ["后三直选的1000个有序结果怎么来", "第一层：和值9–18如何缩小空间", "第二层：跨度2–6如何继续筛选", "实际怎么操作：逐层记录before/after/excluded", "为什么实验参数不等于预测优势", "完成两层后停止临时加条件"],
        "stages": [
            {"id": "sum_9_18", "label": "和值9–18", "atom": "sum_range", "op": "sum_range", "params": {"min": 9, "max": 18}, "basis": "experimental_parameter"},
            {"id": "span_2_6", "label": "跨度2–6", "atom": "span_range", "op": "span_range", "params": {"min": 2, "max": 6}, "basis": "experimental_parameter"},
        ],
        "rule": "SSC-HIST-MECH-3STAR-LAST-V1", "expected": [1000, 670, 396],
    },
    {
        "id": "002", "play": "前三直选", "selector": "前三",
        "family": "V22-STAB-FRONT3-ODD-BIG", "atoms": ["odd_even_filter", "big_small_filter"],
        "title": "分分彩前三直选奇偶大小技巧：1个奇数后再筛2个大号",
        "primary": "分分彩前三直选奇偶大小技巧",
        "secondary": ["分分彩前三直选", "前三奇偶技巧", "前三大小技巧", "时时彩结构筛选"],
        "intent": "看懂分分彩前三直选如何把奇偶个数与大小个数作为两层预冻结结构条件",
        "summary": "从1000个前三有序结果开始，先保留恰好1个奇数，再保留恰好2个大号，展示1000→375→132。",
        "metrics": ["odd_count", "big_count"],
        "outline": ["前三直选的理论结果空间", "第一层：恰好1个奇数怎么筛", "第二层：恰好2个大号怎么筛", "实际怎么操作：结构条件逐层复算", "奇偶大小只是确定性分类", "最后一层完成后停止"],
        "stages": [
            {"id": "odd_1", "label": "恰好1个奇数", "atom": "odd_even_filter", "op": "odd_count", "params": {"count": 1}, "basis": "experimental_parameter"},
            {"id": "big_2", "label": "恰好2个大号", "atom": "big_small_filter", "op": "big_count", "params": {"count": 2}, "basis": "experimental_parameter"},
        ],
        "rule": "SSC-DERIVED-MECH-FRONT3-DIRECT-V1", "expected": [1000, 375, 132],
    },
    {
        "id": "003", "play": "中三直选", "selector": "中三",
        "family": "V22-STAB-MIDDLE3-BIG-DISTINCT", "atoms": ["big_small_filter", "repeat_number"],
        "title": "分分彩中三直选大小重号技巧：1个大号后只留三位全异",
        "primary": "分分彩中三直选大小重号技巧",
        "secondary": ["分分彩中三直选", "中三大小技巧", "中三重号结构", "时时彩筛选"],
        "intent": "看懂分分彩中三直选如何先按大号个数筛选，再用三位全异结构排除重复号码",
        "summary": "从1000个中三有序结果开始，先保留恰好1个大号，再保留三位全异，展示1000→375→300。",
        "metrics": ["big_count", "distinct_count"],
        "outline": ["中三直选位置与1000个结果", "第一层：恰好1个大号", "第二层：三位全异如何排重", "实际怎么操作：先大小后重号结构", "全异是结构条件不是预测结论", "完成两层后停止"],
        "stages": [
            {"id": "big_1", "label": "恰好1个大号", "atom": "big_small_filter", "op": "big_count", "params": {"count": 1}, "basis": "experimental_parameter"},
            {"id": "distinct_3", "label": "三位全异", "atom": "repeat_number", "op": "distinct_count", "params": {"count": 3}, "basis": "experimental_parameter"},
        ],
        "rule": "SSC-DERIVED-MECH-MIDDLE3-DIRECT-V1", "expected": [1000, 375, 300],
    },
    {
        "id": "004", "play": "后三直选", "selector": "后三",
        "family": "V22-STAB-BACK3-POOL-ODD", "atoms": ["compound_selection", "odd_even_filter"],
        "title": "分分彩后三直选数字池奇偶技巧：6码池后筛恰好1个奇数",
        "primary": "分分彩后三直选数字池奇偶技巧",
        "secondary": ["分分彩后三直选", "后三数字池", "后三奇偶技巧", "时时彩复式筛选"],
        "intent": "看懂分分彩后三直选如何先固定6个候选数字，再按奇数个数继续筛选",
        "summary": "从1000个后三有序结果开始，先固定1/2/4/6/8/9六码池，再保留恰好1个奇数，展示1000→216→96。",
        "metrics": ["digit_pool", "odd_count"],
        "outline": ["后三直选的起始结果空间", "第一层：6码池为什么得到216个结果", "第二层：恰好1个奇数为什么剩96个", "实际怎么操作：数字池与奇偶分开核算", "冻结数字池不等于号码预测", "完成两层后停止"],
        "stages": [
            {"id": "pool_124689", "label": "候选数字池1/2/4/6/8/9", "atom": "compound_selection", "op": "digit_pool", "params": {"digits": [1, 2, 4, 6, 8, 9]}, "basis": "experimental_parameter"},
            {"id": "odd_1", "label": "恰好1个奇数", "atom": "odd_even_filter", "op": "odd_count", "params": {"count": 1}, "basis": "experimental_parameter"},
        ],
        "rule": "SSC-HIST-MECH-3STAR-LAST-V1", "expected": [1000, 216, 96],
    },
    {
        "id": "005", "play": "前三直选", "selector": "前三",
        "family": "V22-STAB-FRONT3-SPAN-SUM", "atoms": ["span_range", "sum_range"],
        "title": "分分彩前三直选跨度和值技巧：跨度4–8后再筛和值12–20",
        "primary": "分分彩前三直选跨度和值技巧",
        "secondary": ["分分彩前三直选", "前三跨度技巧", "前三和值技巧", "时时彩范围筛选"],
        "intent": "看懂分分彩前三直选如何先按跨度范围筛选，再按和值区间继续压缩候选",
        "summary": "从1000个前三有序结果开始，先筛跨度4–8，再筛和值12–20，展示1000→660→414。",
        "metrics": ["span_range", "sum_range"],
        "outline": ["前三直选理论空间", "第一层：跨度4–8如何计算", "第二层：和值12–20如何继续筛", "实际怎么操作：先跨度后和值", "参数区间只用于演示复算", "完成两层后停止"],
        "stages": [
            {"id": "span_4_8", "label": "跨度4–8", "atom": "span_range", "op": "span_range", "params": {"min": 4, "max": 8}, "basis": "experimental_parameter"},
            {"id": "sum_12_20", "label": "和值12–20", "atom": "sum_range", "op": "sum_range", "params": {"min": 12, "max": 20}, "basis": "experimental_parameter"},
        ],
        "rule": "SSC-DERIVED-MECH-FRONT3-DIRECT-V1", "expected": [1000, 660, 414],
    },
    {
        "id": "006", "play": "中三直选", "selector": "中三",
        "family": "V22-STAB-MIDDLE3-ODD-DISTINCT", "atoms": ["odd_even_filter", "repeat_number"],
        "title": "分分彩中三直选奇偶重号技巧：2个奇数后排除重复号码",
        "primary": "分分彩中三直选奇偶重号技巧",
        "secondary": ["分分彩中三直选", "中三奇偶技巧", "中三重号技巧", "时时彩结构筛选"],
        "intent": "看懂分分彩中三直选如何先固定奇数个数，再用三位全异结构继续筛选",
        "summary": "从1000个中三有序结果开始，先保留恰好2个奇数，再保留三位全异，展示1000→375→300。",
        "metrics": ["odd_count", "distinct_count"],
        "outline": ["中三直选起始空间", "第一层：恰好2个奇数", "第二层：三位全异排除重复", "实际怎么操作：结构条件逐层复算", "奇偶与重号不代表未来优势", "完成两层后停止"],
        "stages": [
            {"id": "odd_2", "label": "恰好2个奇数", "atom": "odd_even_filter", "op": "odd_count", "params": {"count": 2}, "basis": "experimental_parameter"},
            {"id": "distinct_3", "label": "三位全异", "atom": "repeat_number", "op": "distinct_count", "params": {"count": 3}, "basis": "experimental_parameter"},
        ],
        "rule": "SSC-DERIVED-MECH-MIDDLE3-DIRECT-V1", "expected": [1000, 375, 300],
    },
    {
        "id": "007", "play": "后二组选", "selector": "后二",
        "family": "V22-STAB-BACK2-POOL-SUM", "atoms": ["compound_selection", "sum_range"],
        "title": "分分彩后二组选六码池和值技巧：15注再筛到9注",
        "primary": "分分彩后二组选六码池和值技巧",
        "secondary": ["分分彩后二组选", "后二组选六码", "二星组选和值", "分分彩注数筛选"],
        "intent": "看懂分分彩后二组选如何先固定六码池形成15注，再按对子和值7–14筛选",
        "summary": "从45个后二组选无序对子开始，先固定0/1/4/6/8/9六数字池，再筛对子和值7–14，展示45→15→9。",
        "metrics": ["combination_count", "pair_sum"],
        "outline": ["后二组选45注怎么来", "第一层：六码池为什么是15注", "第二层：对子和值7–14为什么剩9注", "实际怎么操作：数字池与对子和值分开", "注数缩小不等于命中率提高", "完成两层后停止"],
        "stages": [
            {"id": "pool_014689", "label": "候选数字池0/1/4/6/8/9", "atom": "compound_selection", "op": "digit_pool", "params": {"digits": [0, 1, 4, 6, 8, 9]}, "basis": "experimental_parameter"},
            {"id": "pair_sum_7_14", "label": "对子和值7–14", "atom": "sum_range", "op": "pair_sum_range", "params": {"min": 7, "max": 14}, "basis": "experimental_parameter"},
        ],
        "rule": "SSC-HIST-MECH-2STAR-GROUP-V1", "expected": [45, 15, 9],
    },
    {
        "id": "008", "play": "前二组选", "selector": "前二",
        "family": "V22-STAB-FRONT2-POOL-PARITY", "atoms": ["compound_selection", "odd_even_filter"],
        "title": "分分彩前二组选数字池奇偶技巧：六码池后只留一奇一偶",
        "primary": "分分彩前二组选数字池奇偶技巧",
        "secondary": ["分分彩前二组选", "前二组选复式", "前二奇偶技巧", "时时彩注数筛选"],
        "intent": "看懂分分彩前二组选如何先固定六码池，再只保留一奇一偶的无序对子",
        "summary": "从45个前二组选无序对子开始，先固定0/2/3/5/7/8六数字池，再筛一奇一偶，展示45→15→9。",
        "metrics": ["combination_count", "mixed_parity"],
        "outline": ["前二组选45注的来源", "第一层：六码池形成15注", "第二层：一奇一偶筛到9注", "实际怎么操作：无序对子逐层核算", "奇偶结构只是分类条件", "完成两层后停止"],
        "stages": [
            {"id": "pool_023578", "label": "候选数字池0/2/3/5/7/8", "atom": "compound_selection", "op": "digit_pool", "params": {"digits": [0, 2, 3, 5, 7, 8]}, "basis": "experimental_parameter"},
            {"id": "mixed_parity", "label": "一奇一偶", "atom": "odd_even_filter", "op": "mixed_parity", "params": {}, "basis": "experimental_parameter"},
        ],
        "rule": "SSC-DERIVED-MECH-FRONT2-GROUP-V1", "expected": [45, 15, 9],
    },
    {
        "id": "009", "play": "后二组选", "selector": "后二",
        "family": "V22-STAB-BACK2-SUM-PARITY", "atoms": ["sum_range", "odd_even_filter"],
        "title": "分分彩后二组选和值奇偶技巧：和值6–13后再筛一奇一偶",
        "primary": "分分彩后二组选和值奇偶技巧",
        "secondary": ["分分彩后二组选", "后二组选和值", "后二组选奇偶", "二星组选筛选"],
        "intent": "看懂分分彩后二组选如何先按对子和值6–13筛选，再保留一奇一偶组合",
        "summary": "从45个后二组选无序对子开始，先筛对子和值6–13，再筛一奇一偶，展示45→30→16。",
        "metrics": ["pair_sum", "mixed_parity"],
        "outline": ["后二组选理论45注", "第一层：对子和值6–13", "第二层：一奇一偶继续筛选", "实际怎么操作：先和值后奇偶", "确定性空间不等于预测优势", "完成两层后停止"],
        "stages": [
            {"id": "pair_sum_6_13", "label": "对子和值6–13", "atom": "sum_range", "op": "pair_sum_range", "params": {"min": 6, "max": 13}, "basis": "experimental_parameter"},
            {"id": "mixed_parity", "label": "一奇一偶", "atom": "odd_even_filter", "op": "mixed_parity", "params": {}, "basis": "experimental_parameter"},
        ],
        "rule": "SSC-HIST-MECH-2STAR-GROUP-V1", "expected": [45, 30, 16],
    },
    {
        "id": "010", "play": "前二组选", "selector": "前二",
        "family": "V22-STAB-FRONT2-POOL-SUM", "atoms": ["compound_selection", "sum_range"],
        "title": "分分彩前二组选六码池和值技巧：数字池后再筛和值8–12",
        "primary": "分分彩前二组选六码池和值技巧",
        "secondary": ["分分彩前二组选", "前二组选六码", "前二组选和值", "时时彩注数技巧"],
        "intent": "看懂分分彩前二组选如何先固定六码池，再按对子和值8–12筛选无序组合",
        "summary": "从45个前二组选无序对子开始，先固定1/2/3/6/7/9六数字池，再筛对子和值8–12，展示45→15→8。",
        "metrics": ["combination_count", "pair_sum"],
        "outline": ["前二组选45注怎么来", "第一层：六码池为什么得到15注", "第二层：对子和值8–12为什么剩8注", "实际怎么操作：先数字池再和值", "冻结参数不等于选号预测", "完成两层后停止"],
        "stages": [
            {"id": "pool_123679", "label": "候选数字池1/2/3/6/7/9", "atom": "compound_selection", "op": "digit_pool", "params": {"digits": [1, 2, 3, 6, 7, 9]}, "basis": "experimental_parameter"},
            {"id": "pair_sum_8_12", "label": "对子和值8–12", "atom": "sum_range", "op": "pair_sum_range", "params": {"min": 8, "max": 12}, "basis": "experimental_parameter"},
        ],
        "rule": "SSC-DERIVED-MECH-FRONT2-GROUP-V1", "expected": [45, 15, 8],
    },
]


def _fingerprint(case_id: str) -> str:
    return hashlib.sha256(f"v22-stability-10-{case_id}".encode("utf-8")).hexdigest()


def build_stability_blueprint(case: dict) -> dict:
    selector = case["selector"]
    group_play = "组选" in case["play"]
    space_type = "unordered_2digit" if group_play else "ordered_3digit"
    starting_space = 45 if group_play else 1000
    subject_play = case["play"] + "复式" if group_play else case["play"]
    return {
        "blueprint_id": f"BP-V22-STAB-{case['id']}",
        "article_id": f"LCM-STAB-V22-{case['id']}",
        "provider_id": None,
        "lottery": "时时彩",
        "play": case["play"],
        "subject_lottery": "分分彩",
        "subject_play": subject_play,
        "content_type": "technique_article",
        "site_category_key": "tzjq",
        "technique_family": case["family"],
        "technique_atoms": list(case["atoms"]),
        "resolved_selector": selector,
        "selector_basis": "verified_play",
        "source_positions": POSITION_MAP[selector],
        "angle_signature": f"v22-stability-{case['id']}",
        "title": case["title"],
        "slug_seed": f"v22-stability-{case['id']}",
        "primary_keyword": case["primary"],
        "secondary_keywords": list(case["secondary"]),
        "search_intent": case["intent"],
        "information_gain_type": "prefrozen_multistage_filter_case",
        "summary_goal": case["summary"],
        "outline": list(case["outline"]),
        "case_structure": (
            f"selector={selector};metrics={','.join(case['metrics'])};scope=mechanics_only"
        ),
        "case_plan": {
            "supported": [
                {"atom": atom, "metric": metric}
                for atom, metric in zip(case["atoms"], case["metrics"])
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
            "stages": [dict(stage) for stage in case["stages"]],
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


def stability_suite() -> list[tuple[dict, list[int]]]:
    return [(build_stability_blueprint(case), list(case["expected"])) for case in CASES]
