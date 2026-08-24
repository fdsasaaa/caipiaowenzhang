from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.title_seo import audit_public_release_titles, render_audit_markdown


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit formal public-r1 titles without modifying articles")
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()

    report = audit_public_release_titles()
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(render_audit_markdown(report), encoding="utf-8")

    print(json.dumps({
        "formal_public_release_count": report["formal_public_release_count"],
        "titles_starting_with_fenfen": report["titles_starting_with_fenfen"],
        "titles_recommended_for_revision": report["titles_recommended_for_revision"],
        "titles_with_high_similarity": report["titles_with_high_similarity"],
        "titles_with_unsupported_numeric_claims": report["titles_with_unsupported_numeric_claims"],
        "gate_fail_counts": report["gate_fail_counts"],
        "articles_modified": report["articles_modified"],
        "website_side_effects": report["website_side_effects"],
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
