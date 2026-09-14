from app.models.schemas import RepoFile, RepoSummary

EXTENSION_LANGUAGES = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".rb": "Ruby",
    ".php": "PHP",
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".hpp": "C++",
    ".cs": "C#",
    ".swift": "Swift",
    ".m": "Objective-C",
    ".scala": "Scala",
    ".sh": "Shell",
    ".sql": "SQL",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
    ".md": "Markdown",
}


def parse_repo(
    raw_tree: list[str],
    readme: str | None,
    file_contents: dict[str, str],
    repo_url: str,
    branch: str,
) -> RepoSummary:
    file_tree = []
    languages: set[str] = set()

    for path in raw_tree:
        content = file_contents.get(path)
        size = len(content.encode("utf-8")) if content is not None else 0
        file_tree.append(RepoFile(path=path, content=content, size=size))

        language = _infer_language(path)
        if language:
            languages.add(language)

    return RepoSummary(
        repo_url=repo_url,
        default_branch=branch,
        readme=readme,
        file_tree=file_tree,
        languages=sorted(languages),
    )


def _infer_language(path: str) -> str | None:
    for extension, language in EXTENSION_LANGUAGES.items():
        if path.endswith(extension):
            return language
    return None
