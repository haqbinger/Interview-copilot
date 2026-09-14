import base64
import binascii
import logging
import re

import httpx

logger = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com"

EXCLUDED_DIRS = {".git", "node_modules", "__pycache__"}
EXCLUDED_EXTENSIONS = {".png", ".jpg", ".gif", ".ico", ".svg"}


class GitHubClientError(Exception):
    pass


class GitHubClient:
    def __init__(self, token: str):
        self._client = httpx.Client(
            base_url=GITHUB_API_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            timeout=30.0,
        )

    @staticmethod
    def parse_github_url(github_url: str) -> tuple[str, str]:
        match = re.search(r"github\.com[/:]([^/]+)/([^/.]+)", github_url)
        if not match:
            raise GitHubClientError(f"Could not parse owner/repo from URL: {github_url}")
        return match.group(1), match.group(2)

    def get_repo_tree(self, owner: str, repo: str, branch: str) -> list[str]:
        try:
            response = self._client.get(
                f"/repos/{owner}/{repo}/git/trees/{branch}",
                params={"recursive": "1"},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise GitHubClientError(f"Failed to fetch repo tree for {owner}/{repo}: {exc}") from exc

        tree = response.json().get("tree", [])
        paths = [entry["path"] for entry in tree if entry.get("type") == "blob"]
        return [path for path in paths if self._is_included(path)]

    def get_file_content(self, owner: str, repo: str, path: str, branch: str) -> str | None:
        try:
            response = self._client.get(
                f"/repos/{owner}/{repo}/contents/{path}",
                params={"ref": branch},
            )
        except httpx.HTTPError as exc:
            raise GitHubClientError(f"Failed to fetch file content for {path}: {exc}") from exc

        if response.status_code == 404:
            return None
        try:
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise GitHubClientError(f"Failed to fetch file content for {path}: {exc}") from exc

        data = response.json()
        if data.get("encoding") != "base64":
            return None

        try:
            return base64.b64decode(data["content"]).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError):
            return None

    def get_readme(self, owner: str, repo: str, branch: str) -> str | None:
        try:
            response = self._client.get(f"/repos/{owner}/{repo}/readme", params={"ref": branch})
        except httpx.HTTPError as exc:
            raise GitHubClientError(f"Failed to fetch README for {owner}/{repo}: {exc}") from exc

        if response.status_code == 404:
            return None
        try:
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise GitHubClientError(f"Failed to fetch README for {owner}/{repo}: {exc}") from exc

        data = response.json()
        try:
            return base64.b64decode(data["content"]).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError, KeyError):
            return None

    @staticmethod
    def _is_included(path: str) -> bool:
        parts = set(path.split("/"))
        if parts & EXCLUDED_DIRS:
            return False
        return not any(path.endswith(ext) for ext in EXCLUDED_EXTENSIONS)
