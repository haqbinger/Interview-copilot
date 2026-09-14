import json
import logging

from app.models.schemas import StressFollowUpRequest, StressFollowUpResponse

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_TEMPLATE = """You are a skeptical staff engineer and hiring bar-raiser at a top-tier tech \
company. You do not accept vague answers. You challenge every assumption. You are not hostile but you \
are relentless. Your job is to find the boundary of what this candidate actually knows vs what they \
think they know.

Original question:
\"\"\"
{question_text}
\"\"\"

Candidate's answer, verbatim:
\"\"\"
{candidate_answer}
\"\"\"

Evaluation verdict: {verdict}
Missing concepts: {missing_concepts}

Relevant repo context:
Repository: {repo_url}
Languages: {languages}

README:
{readme}

File tree:
{file_list}

File contents:
{file_contents}

Push the candidate on the weakest part of their answer. Respond with ONLY a JSON object (no markdown \
fences, no commentary) with exactly this shape:
{{
  "follow_up": "You said X is scalable. Define scalable. What is the actual bottleneck in your \
architecture at 10x current load?",
  "challenge_type": "scale"
}}

"challenge_type" must be exactly one of: "why", "failure_mode", "alternative", "scale", "tradeoff", \
"contradiction".
"""


def generate_stress_followup(request: StressFollowUpRequest, provider) -> StressFollowUpResponse:
    system_prompt = _build_system_prompt(request)
    response_text = provider.complete(
        system=system_prompt,
        messages=[{"role": "user", "content": "Generate the follow-up challenge now."}],
    )

    try:
        data = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse stress follow-up response as JSON: {exc}") from exc

    try:
        return StressFollowUpResponse(
            follow_up=data["follow_up"],
            challenge_type=data["challenge_type"],
            pressure_level=_pressure_level(request.exchange_number),
        )
    except (TypeError, KeyError) as exc:
        raise ValueError(f"Failed to parse stress follow-up response as JSON: {exc}") from exc


def _pressure_level(exchange_number: int) -> int:
    if exchange_number <= 1:
        return 3
    if exchange_number == 2:
        return 4
    return 5


def _build_system_prompt(request: StressFollowUpRequest) -> str:
    repo_summary = request.repo_summary
    file_list = "\n".join(f"- {f.path}" for f in repo_summary.file_tree)
    file_contents = "\n\n".join(
        f"### {f.path}\n{f.content}" for f in repo_summary.file_tree if f.content is not None
    )

    return SYSTEM_PROMPT_TEMPLATE.format(
        question_text=request.question_text,
        candidate_answer=request.candidate_answer,
        verdict=request.evaluation.verdict,
        missing_concepts=request.evaluation.missing_concepts,
        repo_url=repo_summary.repo_url,
        languages=", ".join(repo_summary.languages),
        readme=repo_summary.readme or "(none)",
        file_list=file_list,
        file_contents=file_contents,
    )
