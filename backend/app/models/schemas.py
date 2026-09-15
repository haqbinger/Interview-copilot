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
    category: str


class RAGMetrics(BaseModel):
    retrieval_precision: float
    answer_faithfulness: float
    chunks_retrieved: int


class AnswerEvaluation(BaseModel):
    question_id: str
    category: str
    score: int = Field(ge=1, le=5)
    verdict: str
    correct_concepts: list[str]
    missing_concepts: list[str]
    misconceptions: list[str]
    follow_up: str
    rag_metrics: RAGMetrics | None = None


class EvaluateAnswerResponse(BaseModel):
    evaluation: AnswerEvaluation
    difficulty_adjustment: int


class CategoryScore(BaseModel):
    category: str
    score: float
    max_score: float


class InterviewReport(BaseModel):
    session_id: str
    overall_score: float
    category_scores: list[CategoryScore]
    strong_areas: list[str]
    weak_areas: list[str]
    misconceptions: list[str]
    revision_plan: list[str]
    follow_up_questions: list[str]
    mode: InterviewMode
    total_questions: int
    answered_questions: int


class GenerateReportRequest(BaseModel):
    session_id: str
    mode: InterviewMode
    repo_summary: RepoSummary
    briefing: BriefingResult
    evaluations: list[AnswerEvaluation]


class StressFollowUpRequest(BaseModel):
    session_id: str
    question_text: str
    candidate_answer: str
    evaluation: AnswerEvaluation
    repo_summary: RepoSummary
    exchange_number: int


class StressFollowUpResponse(BaseModel):
    follow_up: str
    challenge_type: str
    pressure_level: int = Field(ge=1, le=5)


class SessionState(str, Enum):
    INGESTING = "INGESTING"
    EXPLAINING = "EXPLAINING"
    INTERVIEWING = "INTERVIEWING"
    EVALUATING = "EVALUATING"
    REPORTING = "REPORTING"
    COMPLETE = "COMPLETE"


class SessionCreateRequest(BaseModel):
    github_url: str
    mode: InterviewMode
    api_keys: list[dict] | None = None
    groq_api_key: str | None = None
    gemini_api_key: str | None = None
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    deepseek_api_key: str | None = None
    openrouter_api_key: str | None = None
    mistral_api_key: str | None = None
    preferred_provider: str | None = None


class SessionStatusResponse(BaseModel):
    session_id: str
    state: SessionState
    current_question_index: int
    total_questions: int


class AnswerRequest(BaseModel):
    session_id: str
    answer: str


class SessionResponse(BaseModel):
    session_id: str
    state: SessionState
    message: str
    data: dict
    latency_ms: float | None = None
    input_tokens: int | None = None
    estimated_cost_usd: float | None = None
