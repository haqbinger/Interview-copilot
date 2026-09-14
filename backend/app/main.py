import logging

from fastapi import APIRouter, FastAPI, HTTPException

from app.config import Settings, settings
from app.ingestion.briefing_generator import generate_briefing
from app.ingestion.github_client import GitHubClientError
from app.ingestion.ingest_service import fetch_repo_summary
from app.interview.answer_evaluator import evaluate_answer
from app.interview.question_generator import generate_questions
from app.interview.report_generator import generate_report
from app.interview.stress_interviewer import generate_stress_followup
from app.llm.provider import ClaudeProvider, FallbackProvider, GeminiProvider, GroqProvider
from app.models.schemas import (
    AnswerRequest,
    AnswerSubmission,
    EvaluateAnswerResponse,
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    GenerateReportRequest,
    IngestRequest,
    IngestResponse,
    InterviewReport,
    SessionCreateRequest,
    SessionResponse,
    SessionStatusResponse,
    StressFollowUpRequest,
    StressFollowUpResponse,
)
from app.session.runner import (
    SessionNotFoundError,
    get_status,
    start_session,
    submit_answer,
    submit_explanation,
)
from app.session.store import store

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


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/v1/ingest", response_model=IngestResponse)
def ingest(request: IngestRequest) -> IngestResponse:
    try:
        repo_summary = fetch_repo_summary(request.github_url)
    except GitHubClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    try:
        briefing = generate_briefing(repo_summary, provider)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return IngestResponse(repo_summary=repo_summary, briefing=briefing)


@router.post("/api/v1/questions", response_model=GenerateQuestionsResponse)
def questions(request: GenerateQuestionsRequest) -> GenerateQuestionsResponse:
    try:
        return generate_questions(request, provider)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/api/v1/evaluate", response_model=EvaluateAnswerResponse)
def evaluate(submission: AnswerSubmission) -> EvaluateAnswerResponse:
    try:
        return evaluate_answer(submission, provider)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/api/v1/report", response_model=InterviewReport)
def report(request: GenerateReportRequest) -> InterviewReport:
    try:
        return generate_report(request, provider)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/api/v1/stress/followup", response_model=StressFollowUpResponse)
def stress_followup(request: StressFollowUpRequest) -> StressFollowUpResponse:
    try:
        return generate_stress_followup(request, provider)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/api/v1/session/start", response_model=SessionResponse)
def session_start(request: SessionCreateRequest) -> SessionResponse:
    session_id = store.create(request.mode)
    try:
        return start_session(session_id, request.github_url, request.mode, provider)
    except (GitHubClientError, ValueError) as exc:
        store.delete(session_id)
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/api/v1/session/{session_id}/explain", response_model=SessionResponse)
def session_explain(session_id: str, request: AnswerRequest) -> SessionResponse:
    if store.get(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        return submit_explanation(session_id, request.answer, provider)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/api/v1/session/{session_id}/answer", response_model=SessionResponse)
def session_answer(session_id: str, request: AnswerRequest) -> SessionResponse:
    if store.get(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        return submit_answer(session_id, request.answer, provider)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/api/v1/session/{session_id}/status", response_model=SessionStatusResponse)
def session_status(session_id: str) -> SessionStatusResponse:
    try:
        return get_status(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc


app.include_router(router)
