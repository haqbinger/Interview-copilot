from enum import Enum

from pydantic import BaseModel, Field


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


class InterviewMode(str, Enum):
    BEGINNER = "BEGINNER"
    TECHNICAL = "TECHNICAL"
    DEEP_DIVE = "DEEP_DIVE"
    STRESS = "STRESS"


class Question(BaseModel):
    id: str
    text: str
    category: str
    difficulty: int = Field(ge=1, le=5)
    follow_up_hint: str


class QuestionSet(BaseModel):
    mode: InterviewMode
    questions: list[Question]
    session_id: str


class GenerateQuestionsRequest(BaseModel):
    repo_summary: RepoSummary
    briefing: BriefingResult
    candidate_explanation: str
    mode: InterviewMode = InterviewMode.TECHNICAL


class GenerateQuestionsResponse(BaseModel):
    question_set: QuestionSet
    explanation_gaps: list[str]


class AnswerSubmission(BaseModel):
    session_id: str
    question_id: str
    question_text: str
    candidate_answer: str
    repo_summary: RepoSummary


class AnswerEvaluation(BaseModel):
    question_id: str
    score: int = Field(ge=1, le=5)
    verdict: str
    correct_concepts: list[str]
    missing_concepts: list[str]
    misconceptions: list[str]
    follow_up: str


class EvaluateAnswerResponse(BaseModel):
    evaluation: AnswerEvaluation
    difficulty_adjustment: int
