import logging

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import Settings, settings
from app.guardrails.input_validator import validate_answer, validate_api_key, validate_github_url
from app.ingestion.briefing_generator import generate_briefing
from app.ingestion.github_client import GitHubClientError
from app.ingestion.ingest_service import fetch_repo_summary
from app.interview.answer_evaluator import evaluate_answer
from app.interview.question_generator import generate_questions
from app.interview.report_generator import generate_report
from app.interview.stress_interviewer import generate_stress_followup
from app.llm.provider import (
    ClaudeProvider,
    DeepSeekProvider,
    FallbackProvider,
    GeminiProvider,
    GroqProvider,
    MistralProvider,
    OpenAIProvider,
    OpenRouterProvider,
)
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
    "openai": OpenAIProvider,
    "deepseek": DeepSeekProvider,
    "openrouter": OpenRouterProvider,
    "mistral": MistralProvider,
}
PROVIDER_KEYS = {
    "groq": "GROQ_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "mistral": "MISTRAL_API_KEY",
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://interview-copilot-49i7.onrender.com",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)
router = APIRouter()
provider = _build_provider(settings)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/v1/ingest", response_model=IngestResponse)
@limiter.limit("5/minute")
def ingest(request: Request, payload: IngestRequest) -> IngestResponse:
    try:
        repo_summary = fetch_repo_summary(payload.github_url)
    except GitHubClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    try:
        briefing = generate_briefing(repo_summary, provider)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return IngestResponse(repo_summary=repo_summary, briefing=briefing)


@router.post("/api/v1/questions", response_model=GenerateQuestionsResponse)
@limiter.limit("10/minute")
def questions(request: Request, payload: GenerateQuestionsRequest) -> GenerateQuestionsResponse:
    try:
        return generate_questions(payload, provider)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/api/v1/evaluate", response_model=EvaluateAnswerResponse)
@limiter.limit("20/minute")
def evaluate(request: Request, submission: AnswerSubmission) -> EvaluateAnswerResponse:
    try:
        return evaluate_answer(submission, provider)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/api/v1/report", response_model=InterviewReport)
@limiter.limit("10/minute")
def report(request: Request, payload: GenerateReportRequest) -> InterviewReport:
    try:
        return generate_report(payload, provider)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/api/v1/stress/followup", response_model=StressFollowUpResponse)
@limiter.limit("20/minute")
def stress_followup(request: Request, payload: StressFollowUpRequest) -> StressFollowUpResponse:
    try:
        return generate_stress_followup(payload, provider)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/api/v1/session/start", response_model=SessionResponse)
@limiter.limit("5/minute")
def session_start(request: Request, payload: SessionCreateRequest) -> SessionResponse:
    try:
        validate_github_url(payload.github_url)
        if payload.api_keys:
            for entry in payload.api_keys:
                provider_name, key = entry.get("provider"), entry.get("key")
                if provider_name and key:
                    validate_api_key(provider_name, key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    session_id = store.create(payload.mode)
    try:
        response = start_session(
            session_id,
            payload.github_url,
            payload.mode,
            provider,
            api_keys=payload.api_keys,
            groq_api_key=payload.groq_api_key,
            gemini_api_key=payload.gemini_api_key,
            anthropic_api_key=payload.anthropic_api_key,
            openai_api_key=payload.openai_api_key,
            deepseek_api_key=payload.deepseek_api_key,
            openrouter_api_key=payload.openrouter_api_key,
            mistral_api_key=payload.mistral_api_key,
            preferred_provider=payload.preferred_provider,
        )
    except (GitHubClientError, ValueError) as exc:
        store.delete(session_id)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    logger.info(
        f"[session_start] provider={response.data.get('provider')} "
        f"latency={response.latency_ms or 0:.0f}ms tokens={response.input_tokens} "
        f"cost=${response.estimated_cost_usd or 0:.6f} session={session_id}"
    )
    return response


@router.post("/api/v1/session/{session_id}/explain", response_model=SessionResponse)
@limiter.limit("10/minute")
def session_explain(request: Request, session_id: str, payload: AnswerRequest) -> SessionResponse:
    if store.get(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        answer = validate_answer(payload.answer)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        response = submit_explanation(session_id, answer, provider)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    logger.info(
        f"[session_explain] provider={response.data.get('provider')} "
        f"latency={response.latency_ms or 0:.0f}ms tokens={response.input_tokens} "
        f"cost=${response.estimated_cost_usd or 0:.6f} session={session_id}"
    )
    return response


@router.post("/api/v1/session/{session_id}/answer", response_model=SessionResponse)
@limiter.limit("20/minute")
def session_answer(request: Request, session_id: str, payload: AnswerRequest) -> SessionResponse:
    if store.get(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        answer = validate_answer(payload.answer)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        response = submit_answer(session_id, answer, provider)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    logger.info(
        f"[session_answer] provider={response.data.get('provider')} "
        f"latency={response.latency_ms or 0:.0f}ms tokens={response.input_tokens} "
        f"cost=${response.estimated_cost_usd or 0:.6f} session={session_id}"
    )
    return response


@router.get("/api/v1/session/{session_id}/status", response_model=SessionStatusResponse)
@limiter.limit("30/minute")
def session_status(request: Request, session_id: str) -> SessionStatusResponse:
    try:
        return get_status(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc


app.include_router(router)
