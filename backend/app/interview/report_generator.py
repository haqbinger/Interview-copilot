import json
import logging
from collections import defaultdict

from app.models.schemas import CategoryScore, GenerateReportRequest, InterviewReport

logger = logging.getLogger(__name__)

MAX_RAW_SCORE = 5
SCALE = 100

SYSTEM_PROMPT_TEMPLATE = """You are a senior engineer writing a post-interview diagnostic for a candidate \
who was interviewed about their own GitHub project, in {mode} mode.

Repo tech stack:
{tech_stack}

Repo key data flows:
{key_data_flows}

Overall score: {overall_score:.1f}/100

Category scores:
{category_scores}

Per-question evaluations, verbatim:
{evaluations}

Based on this, write a diagnostic for the candidate. Respond with ONLY a JSON object (no markdown \
fences, no commentary) with exactly this shape:
{{
  "strong_areas": ["..."],
  "weak_areas": ["..."],
  "misconceptions": ["..."],
  "revision_plan": ["..."],
  "follow_up_questions": ["..."]
}}

The revision_plan must be concrete and actionable — name specific topics, techniques, or concepts from \
this repo the candidate should study, not generic advice like "practice more" or "read documentation".
"""


def generate_report(request: GenerateReportRequest, provider) -> InterviewReport:
    category_scores = _compute_category_scores(request.evaluations)
    overall_score = _compute_overall_score(request.evaluations)

    system_prompt = _build_system_prompt(request, overall_score, category_scores)
    response_text = provider.complete(
        system=system_prompt,
        messages=[{"role": "user", "content": "Write the diagnostic now."}],
    )

    try:
        data = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse report response as JSON: {exc}") from exc

    try:
        return InterviewReport(
            session_id=request.session_id,
            overall_score=overall_score,
            category_scores=category_scores,
            mode=request.mode,
            total_questions=len(request.evaluations),
            answered_questions=len(request.evaluations),
            **data,
        )
    except TypeError as exc:
        raise ValueError(f"Failed to parse report response as JSON: {exc}") from exc


def _compute_overall_score(evaluations: list) -> float:
    if not evaluations:
        return 0.0
    mean_raw = sum(e.score for e in evaluations) / len(evaluations)
    return (mean_raw / MAX_RAW_SCORE) * SCALE


def _compute_category_scores(evaluations: list) -> list[CategoryScore]:
    by_category = defaultdict(list)
    for evaluation in evaluations:
        by_category[evaluation.category].append(evaluation.score)

    return [
        CategoryScore(
            category=category,
            score=(sum(scores) / len(scores) / MAX_RAW_SCORE) * SCALE,
            max_score=float(SCALE),
        )
        for category, scores in by_category.items()
    ]


def _build_system_prompt(
    request: GenerateReportRequest,
    overall_score: float,
    category_scores: list[CategoryScore],
) -> str:
    category_score_lines = "\n".join(
        f"- {cs.category}: {cs.score:.1f}/{cs.max_score:.0f}" for cs in category_scores
    )

    evaluation_lines = "\n\n".join(
        f"Question {e.question_id} ({e.category}, score {e.score}/5): {e.verdict}\n"
        f"Correct concepts: {e.correct_concepts}\n"
        f"Missing concepts: {e.missing_concepts}\n"
        f"Misconceptions: {e.misconceptions}"
        for e in request.evaluations
    )

    return SYSTEM_PROMPT_TEMPLATE.format(
        mode=request.mode.value,
        tech_stack=", ".join(request.briefing.tech_stack),
        key_data_flows="\n".join(f"- {flow}" for flow in request.briefing.key_data_flows),
        overall_score=overall_score,
        category_scores=category_score_lines,
        evaluations=evaluation_lines,
    )
