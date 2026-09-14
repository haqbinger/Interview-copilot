import logging

from fastapi import APIRouter, FastAPI, HTTPException

from app.config import Settings, settings
from app.ingestion.briefing_generator import generate_briefing
from app.ingestion.github_client import GitHubClient, GitHubClientError
from app.ingestion.repo_parser import parse_repo
from app.llm.provider import ClaudeProvider, FallbackProvider, GeminiProvider, GroqProvider
from app.models.schemas import IngestRequest, IngestResponse

logger = logging.getLogger(__name__)

PROVIDER_CLASSES = {
    "groq": GroqProvider,
    "gemini": GeminiProvider,
    "claude": ClaudeProvider,
}
PROVIDER_KEYS = {
    "groq": "GROQ_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
}


def _build_provider(config: Settings) -> FallbackProvider:
    provider_names = [name.strip() for name in config.PROVIDER_PRIORITY.split(",") if name.strip()]
    providers = []
    for name in provider_names:
        if name not in PROVIDER_CLASSES:
            raise ValueError(f"Unknown provider in PROVIDER_PRIORITY: {name}")
        if getattr(config, PROVIDER_KEYS[name]):
            providers.append(PROVIDER_CLASSES[name](config=config))
    if not providers:
        raise ValueError("No providers in PROVIDER_PRIORITY have a configured API key")
    return FallbackProvider(providers)


app = FastAPI()
router = APIRouter()
provider = _build_provider(settings)

# M1 assumes the default branch is "main"; no repo-metadata lookup is in scope for github_client.py yet.
DEFAULT_BRANCH = "main"
ALWAYS_INCLUDED_EXTENSIONS = (".md", ".yml", ".yaml", ".toml", ".json")
MAX_LINES = 50


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/v1/ingest", response_model=IngestResponse)
def ingest(request: IngestRequest) -> IngestResponse:
    github_client = GitHubClient(token=settings.GITHUB_TOKEN)

    try:
        owner, repo = GitHubClient.parse_github_url(request.github_url)
        tree = github_client.get_repo_tree(owner, repo, DEFAULT_BRANCH)
        readme = github_client.get_readme(owner, repo, DEFAULT_BRANCH)

        file_contents: dict[str, str] = {}
        for path in tree:
            content = github_client.get_file_content(owner, repo, path, DEFAULT_BRANCH)
            if content is None:
                continue
            if path.endswith(ALWAYS_INCLUDED_EXTENSIONS) or content.count("\n") < MAX_LINES:
                file_contents[path] = content
    except GitHubClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    repo_summary = parse_repo(
        raw_tree=tree,
        readme=readme,
        file_contents=file_contents,
        repo_url=request.github_url,
        branch=DEFAULT_BRANCH,
    )

    try:
        briefing = generate_briefing(repo_summary, provider)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return IngestResponse(repo_summary=repo_summary, briefing=briefing)


app.include_router(router)
