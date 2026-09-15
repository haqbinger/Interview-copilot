import logging

from app.guardrails.output_validator import validate_llm_json
from app.llm.provider import ClaudeProvider
from app.models.schemas import BriefingResult, RepoSummary

logger = logging.getLogger(__name__)

MAX_CHARS = 12000
TRUNCATION_SUFFIX = "...[truncated for context limit]"

SYSTEM_PROMPT = """You are an assistant preparing an interviewer to discuss a candidate's GitHub project.

You will be given the repo's README, file tree, and selected file contents. Analyze the repo and \
respond with ONLY a JSON object (no markdown fences, no commentary) with exactly these keys:

- "tech_stack": array of strings naming the languages, frameworks, and major libraries used
- "key_data_flows": array of strings, each describing one significant data flow or interaction \
between components in the system
- "opening_prompt": a single string the interviewer will read aloud to open the conversation, \
asking the candidate to explain their project in their own words. It should invite the candidate to \
cover, in their own way: (1) the problem the project solves, (2) the overall architecture, \
(3) the key design decisions and tradeoffs they made, (4) the most challenging part to build, \
and (5) what they would do differently or improve with more time.
"""


def generate_briefing(repo_summary: RepoSummary, provider: ClaudeProvider) -> BriefingResult:
    user_message = _build_user_message(repo_summary)
    if len(user_message) > MAX_CHARS:
        user_message = user_message[:MAX_CHARS] + TRUNCATION_SUFFIX

    response_text = provider.complete(
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    data = validate_llm_json(response_text, ["tech_stack", "key_data_flows", "opening_prompt"])
    try:
        return BriefingResult(**data)
    except TypeError as exc:
        raise ValueError(f"Failed to parse briefing response as JSON: {exc}") from exc


def _build_user_message(repo_summary: RepoSummary) -> str:
    file_list = "\n".join(f"- {f.path}" for f in repo_summary.file_tree)
    file_contents = "\n\n".join(
        f"### {f.path}\n{f.content}" for f in repo_summary.file_tree if f.content is not None
    )

    return f"""Repository: {repo_summary.repo_url}
Languages: {", ".join(repo_summary.languages)}

README:
{repo_summary.readme or "(none)"}

File tree:
{file_list}

File contents:
{file_contents}
"""
