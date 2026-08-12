from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MultiStageQualityReport:
    passed: bool
    score: int
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def evaluate_multistage(packet: dict, article: dict) -> MultiStageQualityReport:
    practicality = packet.get("practicality") or {}
    result = practicality.get("filter_pipeline_result")
    if not isinstance(result, dict):
        return MultiStageQualityReport(False, 0, errors=["V2.2 filter_pipeline_result missing"])

    errors: list[str] = []
    warnings: list[str] = []
    score = 100
    content = str(article.get("content") or "")
    guidance = article.get("practical_guidance") or {}

    start = result.get("starting_space")
    final = result.get("final_space")
    total_excluded = result.get("total_excluded")
    if str(start) not in str(guidance.get("starting_space") or ""):
        errors.append("practical_guidance.starting_space does not match V2.2 pipeline start")
        score -= 20
    if str(final) not in str(guidance.get("after_primary_filter_space") or ""):
        errors.append("practical_guidance.after_primary_filter_space does not match V2.2 pipeline final space")
        score -= 20
    if total_excluded is not None and str(total_excluded) not in content:
        warnings.append("article does not state total candidates excluded by full pipeline")
        score -= 4

    last_position = -1
    for stage in result.get("stages", []):
        stage_id = stage.get("id")
        before = stage.get("before_space")
        after = stage.get("after_space")
        excluded = stage.get("excluded_space")
        label = str(stage.get("label") or stage_id or "")

        missing = [
            value for value in (before, after, excluded)
            if value is not None and str(value) not in content
        ]
        if missing:
            errors.append(
                f"stage {stage_id} missing exact candidate-space numbers in content: {missing}"
            )
            score -= 18

        # Require the stage's resulting count to appear in stage order. This is
        # intentionally simple and deterministic; prose can vary but the math
        # sequence cannot be rearranged.
        marker = str(after)
        position = content.find(marker, max(0, last_position + 1)) if after is not None else -1
        if position < 0:
            errors.append(f"stage {stage_id} after_space is not presented in pipeline order")
            score -= 10
        else:
            last_position = position

        if label and label not in content:
            warnings.append(f"stage {stage_id} label not written verbatim; verify explanation remains clear")
            score -= 2

    stop_condition = str(guidance.get("stop_condition") or "")
    if not any(term in stop_condition for term in ("最后", "末层", "第二层", "完成", "停止", "停下")):
        errors.append("V2.2 stop_condition must tell reader to stop after the prefrozen pipeline")
        score -= 12

    next_policy = str(guidance.get("next_step_policy") or "")
    if not any(term in next_policy for term in ("新增", "新条件", "新的")):
        errors.append("V2.2 next_step_policy must govern any filter beyond the prefrozen pipeline")
        score -= 8

    passed = not errors and score >= 90
    return MultiStageQualityReport(
        passed=passed,
        score=max(0, score),
        errors=list(dict.fromkeys(errors)),
        warnings=list(dict.fromkeys(warnings)),
    )
