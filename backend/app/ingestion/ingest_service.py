import logging

from app.config import settings
from app.ingestion.github_client import GitHubClient
from app.ingestion.repo_parser import parse_repo
from app.models.schemas import RepoSummary

logger = logging.getLogger(__name__)

# M1 assumes the default branch is "main"; no repo-metadata lookup is in scope for github_client.py yet.
DEFAULT_BRANCH = "main"
ALWAYS_INCLUDED_EXTENSIONS = (".md", ".yml", ".yaml", ".toml", ".json")
MAX_BYTES = 8_000


def fetch_repo_summary(github_url: str) -> RepoSummary:
    github_client = GitHubClient(token=settings.GITHUB_TOKEN)
    owner, repo = GitHubClient.parse_github_url(github_url)
    tree = github_client.get_repo_tree(owner, repo, DEFAULT_BRANCH)
    readme = github_client.get_readme(owner, repo, DEFAULT_BRANCH)

    file_contents: dict[str, str] = {}
    for path in tree:
        content = github_client.get_file_content(owner, repo, path, DEFAULT_BRANCH)
        if content is None:
            continue
        if path.endswith(ALWAYS_INCLUDED_EXTENSIONS) or len(content.encode("utf-8")) < MAX_BYTES:
            file_contents[path] = content

    return parse_repo(
        raw_tree=tree,
        readme=readme,
        file_contents=file_contents,
        repo_url=github_url,
        branch=DEFAULT_BRANCH,
    )
