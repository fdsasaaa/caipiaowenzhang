from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rows(path: Path):
    paths = []
    if path.exists():
        paths.append(path)
    paths.extend(sorted(path.parent.glob(path.stem + ".part-*.jsonl")))
    for p in paths:
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                yield json.loads(line)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--coverage", type=Path, default=ROOT / "knowledge/coverage/brbcw.json")
    ap.add_argument("--clusters", type=Path, default=ROOT / "knowledge/technique_clusters/brbcw.jsonl")
    ap.add_argument("--output", type=Path, default=ROOT / "knowledge/coverage/brbcw_report.md")
    args = ap.parse_args()
    cov = json.loads(args.coverage.read_text(encoding="utf-8"))
    clusters = list(rows(args.clusters))
    family_counts = Counter()
    family_sources = Counter()
    for c in clusters:
        family_counts[c.get("family_id", "unknown")] += 1
        family_sources[c.get("family_id", "unknown")] += c.get("source_count", 0)
    top = sorted(clusters, key=lambda x: (-x.get("source_count", 0), x["cluster_id"]))[:50]
    out = [
        "# brbcw 知识抽取报告\n",
        f"- 精选来源：**{cov['sources']}**",
        f"- 有可识别技巧原子的来源：**{cov['sources_with_atoms']}**",
        f"- 暂未识别原子的来源：**{cov['sources_without_atoms']}**",
        f"- 含夸张/盈利/百分比等风险声明的来源：**{cov['sources_with_risk_flags']}**",
        f"- 精细方法簇：**{cov['clusters']}**",
        f"- 方法家族（仅按技巧原子组合）：**{len(family_counts)}**",
        "",
        "## 说明",
        "",
        "这些数字代表来源中的**候选经验结构**，不是已证明有效的方法。任何成稿前都必须绑定已核验玩法规则；涉及命中率、赔率、奖金、盈利的来源说法默认不可信。",
        "",
        "## 技巧原子覆盖",
        "",
    ]
    for name, count in sorted(cov["technique_atoms"].items(), key=lambda kv: (-kv[1], kv[0])):
        out.append(f"- `{name}`：{count}")
    out += ["", "## 来源最多的50个精细方法簇", ""]
    for c in top:
        out.append(f"- **{c['source_count']}篇** | `{c['cluster_id']}` | {c['signature']} | 风险声明率 {c['risk_rate']:.1%}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "families": len(family_counts), "clusters": len(clusters)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
