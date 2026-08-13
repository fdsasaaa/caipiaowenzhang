from pathlib import Path

path = Path("engine/production_controller.py")
text = path.read_text(encoding="utf-8")


def replace_once(old: str, new: str) -> None:
    global text
    assert old in text, f"resume marker missing: {old[:120]!r}"
    text = text.replace(old, new, 1)


# PR #68 inserted provider_response_id before the original angle patch was written.
replace_once(
    '''                    "multistage_score": multistage_score,
                    "provider_response_id": response_id or None,
                    "errors": approval.errors,
''',
    '''                    "multistage_score": multistage_score,
                    "angle_score": getattr(approval, "angle_score", None),
                    "provider_response_id": response_id or None,
                    "errors": approval.errors,
''',
)

# Keep terminology rejections equally auditable even though they were approved by
# the content gates before the public-terminology check.
replace_once(
    '''                    "multistage_score": multistage_score,
                    "provider_response_id": response_id or None,
                    "errors": terminology_errors,
''',
    '''                    "multistage_score": multistage_score,
                    "angle_score": getattr(approval, "angle_score", None),
                    "provider_response_id": response_id or None,
                    "errors": terminology_errors,
''',
)

replace_once(
    '''                "multistage_score": multistage_score,
                "provider_response_id": response_id or None,
                "primary_keyword": package.get("primary_keyword"),
''',
    '''                "multistage_score": multistage_score,
                "angle_score": getattr(approval, "angle_score", None),
                "provider_response_id": response_id or None,
                "primary_keyword": package.get("primary_keyword"),
''',
)

replace_once(
    '''                "primary_seo_cluster_id": package.get("primary_seo_cluster_id"),
''',
    '''                "primary_seo_cluster_id": package.get("primary_seo_cluster_id"),
                "information_gain_type": package.get("information_gain_type"),
''',
)

replace_once(
    '''    multistage_scores = [int(row["multistage_score"]) for row in successful_rows if row.get("multistage_score") is not None]
''',
    '''    multistage_scores = [int(row["multistage_score"]) for row in successful_rows if row.get("multistage_score") is not None]
    angle_scores = [int(row["angle_score"]) for row in successful_rows if row.get("angle_score") is not None]
    angle_distribution = Counter(str(row.get("information_gain_type") or "legacy") for row in successful_rows)
''',
)

replace_once(
    '''        "multistage_score_average": round(sum(multistage_scores) / len(multistage_scores), 2) if multistage_scores else None,
''',
    '''        "multistage_score_average": round(sum(multistage_scores) / len(multistage_scores), 2) if multistage_scores else None,
        "angle_score_average": round(sum(angle_scores) / len(angle_scores), 2) if angle_scores else None,
        "article_angle_distribution": dict(angle_distribution),
''',
)

path.write_text(text, encoding="utf-8")
print("resumed audited article angle patch after PR68 controller marker")
