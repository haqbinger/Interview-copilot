import logging
import uuid

from app.guardrails.output_validator import validate_llm_json
from app.models.schemas import (
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    InterviewMode,
    QuestionSet,
)

logger = logging.getLogger(__name__)

MODE_CONFIG = {
    InterviewMode.BEGINNER: {
        "count": 10,
        "difficulty_range": "1-2",
        "focus": "what the project does, why it was built, and a high-level overview of how it works",
        "tone": "friendly and encouraging",
    },
    InterviewMode.TECHNICAL: {
        "count": 15,
        "difficulty_range": "2-4",
        "focus": "specific implementation decisions and how components interact",
        "tone": "professional and curious",
    },
    InterviewMode.DEEP_DIVE: {
        "count": 15,
        "difficulty_range": "3-5",
        "focus": "failure modes, edge cases, and how the system behaves at scale",
        "tone": "probing and detail-oriented",
    },
    InterviewMode.STRESS: {
        "count": 12,
        "difficulty_range": "4-5",
        "focus": "rigorously challenging every decision the candidate made",
        "tone": "skeptical senior engineer who challenges every decision",
    },
}

SYSTEM_PROMPT_TEMPLATE = """You are a senior engineer conducting a technical interview about the candidate's \
own GitHub project.

Repo tech stack:
{tech_stack}

Repo key data flows:
{key_data_flows}
{code_context_section}
The candidate was asked to explain their project in their own words. Here is what they said, verbatim:
\"\"\"
{candidate_explanation}
\"\"\"

Compare what the repo actually does against what the candidate said. Identify anything they got wrong, \
oversimplified, or left out entirely — these are the explanation gaps.

Generate exactly {count} interview questions grounded in the actual repo (not generic questions). \
Difficulty must be within the range {difficulty_range} (1 is easiest, 5 is hardest). Focus the questions \
on {focus}. Adopt a {tone} tone throughout.

Respond with ONLY a JSON object (no markdown fences, no commentary) with exactly this shape:
{{
  "questions": [
    {{
      "id": "q1",
      "text": "...",
      "category": "architecture|debugging|tradeoffs|code|deployment",
      "difficulty": 3,
      "follow_up_hint": "..."
    }}
  ],
  "explanation_gaps": ["gap1", "gap2"]
}}
"""


def generate_questions(
    request: GenerateQuestionsRequest,
    provider,
    repo_context_chunks: list[str] | None = None,
) -> GenerateQuestionsResponse:
    mode_config = MODE_CONFIG[request.mode]

    code_context_section = ""
    if repo_context_chunks:
        joined_chunks = "\n---\n".join(repo_context_chunks[:2])[:800]
        code_context_section = (
            "\nRelevant code context (retrieved from the repo via semantic search):\n"
            + joined_chunks
            + "\n"
        )

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        tech_stack=", ".join(request.briefing.tech_stack),
        key_data_flows="\n".join(f"- {flow}" for flow in request.briefing.key_data_flows),
        code_context_section=code_context_section,
        candidate_explanation=request.candidate_explanation,
        count=mode_config["count"],
        difficulty_range=mode_config["difficulty_range"],
        focus=mode_config["focus"],
        tone=mode_config["tone"],
    )

    response_text = provider.complete(
        system=system_prompt,
        messages=[{"role": "user", "content": "Generate the interview questions now."}],
    )

    data = validate_llm_json(response_text, ["questions", "explanation_gaps"])
    try:
        question_set = QuestionSet(
            mode=request.mode,
            questions=data["questions"],
            session_id=str(uuid.uuid4()),
        )
        return GenerateQuestionsResponse(
            question_set=question_set,
            explanation_gaps=data["explanation_gaps"],
        )
    except TypeError as exc:
        raise ValueError(f"Failed to parse question generation response as JSON: {exc}") from exc
