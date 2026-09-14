import json
import logging

from app.models.schemas import AnswerEvaluation, AnswerSubmission, EvaluateAnswerResponse

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_TEMPLATE = """You are a senior engineer grading a candidate's answer during a technical \
interview about their own GitHub project.

Question asked:
\"\"\"
{question_text}
\"\"\"

Candidate's answer, verbatim:
\"\"\"
{candidate_answer}
\"\"\"

Relevant repo context:
Repository: {repo_url}
Languages: {languages}

README:
{readme}

File tree:
{file_list}

File contents:
{file_contents}

Grade the answer against what the repo actually does. Respond with ONLY a JSON object (no markdown \
fences, no commentary) with exactly this shape:
{{
  "score": 3,
  "verdict": "Partial — correct on X but missed Y",
  "correct_concepts": ["..."],
  "missing_concepts": ["..."],
  "misconceptions": ["..."],
  "follow_up": "You mentioned X. In this project, what happens when Y?"
}}

"score" is an integer from 1 (wrong or no understanding) to 5 (complete and accurate).
"""


def evaluate_answer(submission: AnswerSubmission, provider) -> EvaluateAnswerResponse:
    system_prompt = _build_system_prompt(submission)
    response_text = provider.complete(
        system=system_prompt,
        messages=[{"role": "user", "content": "Grade the answer now."}],
    )

    try:
        data = json.loads(response_text)
        evaluation = AnswerEvaluation(
            question_id=submission.question_id,
            category=submission.category,
            **data,
        )
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError(f"Failed to parse answer evaluation response as JSON: {exc}") from exc

    return EvaluateAnswerResponse(
        evaluation=evaluation,
        difficulty_adjustment=_difficulty_adjustment(evaluation.score),
    )


def _difficulty_adjustment(score: int) -> int:
    if score >= 4:
        return 1
    if score <= 2:
        return -1
    return 0


def _build_system_prompt(submission: AnswerSubmission) -> str:
    repo_summary = submission.repo_summary
    file_list = "\n".join(f"- {f.path}" for f in repo_summary.file_tree)
    file_contents = "\n\n".join(
        f"### {f.path}\n{f.content}" for f in repo_summary.file_tree if f.content is not None
    )

    return SYSTEM_PROMPT_TEMPLATE.format(
        question_text=submission.question_text,
        candidate_answer=submission.candidate_answer,
        repo_url=repo_summary.repo_url,
        languages=", ".join(repo_summary.languages),
        readme=repo_summary.readme or "(none)",
        file_list=file_list,
        file_contents=file_contents,
    )
