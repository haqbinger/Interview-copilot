import logging

from app.guardrails.output_validator import validate_llm_json
from app.models.schemas import AnswerEvaluation, AnswerSubmission, EvaluateAnswerResponse, RAGMetrics
from app.rag.evaluator import compute_answer_faithfulness, compute_retrieval_precision

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
{repo_context_section}
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


def evaluate_answer(
    submission: AnswerSubmission,
    provider,
    repo_context_chunks: list[str] | None = None,
) -> EvaluateAnswerResponse:
    system_prompt = _build_system_prompt(submission, repo_context_chunks)
    response_text = provider.complete(
        system=system_prompt,
        messages=[{"role": "user", "content": "Grade the answer now."}],
    )

    data = validate_llm_json(
        response_text,
        ["score", "verdict", "correct_concepts", "missing_concepts", "misconceptions", "follow_up"],
    )
    try:
        evaluation = AnswerEvaluation(
            question_id=submission.question_id,
            category=submission.category,
            **data,
        )
    except TypeError as exc:
        raise ValueError(f"Failed to parse answer evaluation response as JSON: {exc}") from exc

    if repo_context_chunks:
        rag_metrics = RAGMetrics(
            retrieval_precision=compute_retrieval_precision(repo_context_chunks, data),
            answer_faithfulness=compute_answer_faithfulness(
                submission.candidate_answer, evaluation.correct_concepts
            ),
            chunks_retrieved=len(repo_context_chunks),
        )
        evaluation = evaluation.model_copy(update={"rag_metrics": rag_metrics})

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


def _build_system_prompt(
    submission: AnswerSubmission,
    repo_context_chunks: list[str] | None = None,
) -> str:
    repo_summary = submission.repo_summary
    file_list = "\n".join(f"- {f.path}" for f in repo_summary.file_tree)
    file_contents = "\n\n".join(
        f"### {f.path}\n{f.content}" for f in repo_summary.file_tree if f.content is not None
    )

    repo_context_section = ""
    if repo_context_chunks:
        joined_chunks = "\n---\n".join(repo_context_chunks[:2])[:800]
        repo_context_section = (
            "\nRELEVANT CODE CONTEXT (retrieved via semantic search):\n" + joined_chunks + "\n"
        )

    return SYSTEM_PROMPT_TEMPLATE.format(
        question_text=submission.question_text,
        candidate_answer=submission.candidate_answer,
        repo_url=repo_summary.repo_url,
        languages=", ".join(repo_summary.languages),
        readme=repo_summary.readme or "(none)",
        file_list=file_list,
        file_contents=file_contents,
        repo_context_section=repo_context_section,
    )
