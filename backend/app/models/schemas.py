from pydantic import BaseModel


class RepoFile(BaseModel):
    path: str
    content: str | None
    size: int


class RepoSummary(BaseModel):
    repo_url: str
    default_branch: str
    readme: str | None
    file_tree: list[RepoFile]
    languages: list[str]


class BriefingResult(BaseModel):
    tech_stack: list[str]
    key_data_flows: list[str]
    opening_prompt: str


class IngestRequest(BaseModel):
    github_url: str


class IngestResponse(BaseModel):
    repo_summary: RepoSummary
    briefing: BriefingResult
