import logging

from app.config import settings
from app.llm.provider import (
    ClaudeProvider,
    DeepSeekProvider,
    FallbackProvider,
    GeminiProvider,
    GroqProvider,
    MistralProvider,
    OpenAIProvider,
    OpenRouterProvider,
    get_last_call_meta,
)
from app.models.schemas import (
    InterviewMode,
    SessionResponse,
    SessionState,
    SessionStatusResponse,
)
from app.session.graph import compiled_graph
from app.session.provider_registry import register as register_provider
from app.session.store import store

logger = logging.getLogger(__name__)

USER_PROVIDER_BUILDERS = {
    "groq": lambda key: GroqProvider(config=settings.model_copy(update={"GROQ_API_KEY": key})),
    "gemini": lambda key: GeminiProvider(config=settings.model_copy(update={"GEMINI_API_KEY": key})),
    "claude": lambda key: ClaudeProvider(config=settings.model_copy(update={"ANTHROPIC_API_KEY": key})),
    "openai": lambda key: OpenAIProvider(config=settings.model_copy(update={"OPENAI_API_KEY": key})),
    "deepseek": lambda key: DeepSeekProvider(config=settings.model_copy(update={"DEEPSEEK_API_KEY": key})),
    "openrouter": lambda key: OpenRouterProvider(
        config=settings.model_copy(update={"OPENROUTER_API_KEY": key})
    ),
    "mistral": lambda key: MistralProvider(config=settings.model_copy(update={"MISTRAL_API_KEY": key})),
}


class SessionNotFoundError(Exception):
    pass


def _config(session_id: str) -> dict:
    return {"configurable": {"thread_id": session_id}}


def _build_provider_from_api_keys(default_provider, api_keys: list[dict]):
    providers = []
    for entry in api_keys:
        name = entry.get("provider")
        key = entry.get("key")
        if not name or not key or name not in USER_PROVIDER_BUILDERS:
            continue
        providers.append(USER_PROVIDER_BUILDERS[name](key))

    fallback_providers = getattr(default_provider, "providers", [default_provider])
    providers.extend(fallback_providers)
    return FallbackProvider(providers)


def _build_session_provider(
    default_provider,
    api_keys: list[dict] | None,
    groq_api_key: str | None,
    gemini_api_key: str | None,
    anthropic_api_key: str | None,
    openai_api_key: str | None,
    deepseek_api_key: str | None,
    openrouter_api_key: str | None,
    mistral_api_key: str | None,
    preferred_provider: str | None,
):
    if api_keys:
        return _build_provider_from_api_keys(default_provider, api_keys)

    supplied = {
        "groq": groq_api_key,
        "gemini": gemini_api_key,
        "claude": anthropic_api_key,
        "openai": openai_api_key,
        "deepseek": deepseek_api_key,
        "openrouter": openrouter_api_key,
        "mistral": mistral_api_key,
    }
    supplied = {name: key for name, key in supplied.items() if key}

    if not supplied:
        return default_provider

    order = []
    if preferred_provider in supplied:
        order.append(preferred_provider)
    order += [name for name in supplied if name not in order]

    providers = [USER_PROVIDER_BUILDERS[name](supplied[name]) for name in order]
    return FallbackProvider(providers)


def start_session(
    session_id: str,
    github_url: str,
    mode: InterviewMode,
    provider,
    api_keys: list[dict] | None = None,
    groq_api_key: str | None = None,
    gemini_api_key: str | None = None,
    anthropic_api_key: str | None = None,
    openai_api_key: str | None = None,
    deepseek_api_key: str | None = None,
    openrouter_api_key: str | None = None,
    mistral_api_key: str | None = None,
    preferred_provider: str | None = None,
) -> SessionResponse:
    session_provider = _build_session_provider(
        provider,
        api_keys,
        groq_api_key,
        gemini_api_key,
        anthropic_api_key,
        openai_api_key,
        deepseek_api_key,
        openrouter_api_key,
        mistral_api_key,
        preferred_provider,
    )
    register_provider(session_id, session_provider)
    initial_state = {
        "session_id": session_id,
        "state": SessionState.INGESTING.value,
        "mode": mode.value,
        "github_url": github_url,
        "repo_summary": None,
        "briefing": None,
        "candidate_explanation": None,
        "question_set": None,
        "current_question_index": 0,
        "current_question": None,
        "evaluations": [],
        "report": None,
        "current_input": None,
        "rag_enabled": False,
    }
    compiled_graph.invoke(initial_state, _config(session_id))
    result = compiled_graph.get_state(_config(session_id)).values
    meta = get_last_call_meta()

    store.update(
        session_id,
        state=SessionState(result["state"]),
        current_question_index=result["current_question_index"],
    )

    return SessionResponse(
        session_id=session_id,
        state=SessionState(result["state"]),
        message="Repo ingested. Please explain the project in your own words.",
        data={
            "briefing": result["briefing"],
            "opening_prompt": result["briefing"]["opening_prompt"],
            "provider": meta.get("provider"),
        },
        latency_ms=meta.get("latency_ms"),
        input_tokens=meta.get("input_tokens"),
        estimated_cost_usd=meta.get("estimated_cost_usd"),
    )


def submit_explanation(session_id: str, explanation: str, provider) -> SessionResponse:
    register_provider(session_id, provider)
    config = _config(session_id)
    compiled_graph.update_state(config, {"current_input": explanation})
    compiled_graph.invoke(None, config)
    result = compiled_graph.get_state(_config(session_id)).values
    meta = get_last_call_meta()

    store.update(
        session_id,
        state=SessionState(result["state"]),
        candidate_explanation=result["candidate_explanation"],
        question_set=result["question_set"],
        current_question_index=result["current_question_index"],
    )

    return SessionResponse(
        session_id=session_id,
        state=SessionState(result["state"]),
        message="First question ready.",
        data={"question": result["current_question"], "provider": meta.get("provider")},
        latency_ms=meta.get("latency_ms"),
        input_tokens=meta.get("input_tokens"),
        estimated_cost_usd=meta.get("estimated_cost_usd"),
    )


def submit_answer(session_id: str, answer: str, provider) -> SessionResponse:
    register_provider(session_id, provider)
    config = _config(session_id)
    compiled_graph.update_state(config, {"current_input": answer})
    compiled_graph.invoke(None, config)
    result = compiled_graph.get_state(_config(session_id)).values
    meta = get_last_call_meta()

    store.update(
        session_id,
        state=SessionState(result["state"]),
        evaluations=result["evaluations"],
        current_question_index=result["current_question_index"],
        report=result["report"],
    )

    latest_evaluation = result["evaluations"][-1] if result["evaluations"] else None

    if result["state"] == SessionState.COMPLETE.value:
        return SessionResponse(
            session_id=session_id,
            state=SessionState(result["state"]),
            message="Interview complete. Final report ready.",
            data={
                "report": result["report"],
                "evaluation": latest_evaluation,
                "provider": meta.get("provider"),
            },
            latency_ms=meta.get("latency_ms"),
            input_tokens=meta.get("input_tokens"),
            estimated_cost_usd=meta.get("estimated_cost_usd"),
        )

    return SessionResponse(
        session_id=session_id,
        state=SessionState(result["state"]),
        message="Next question ready.",
        data={
            "question": result["current_question"],
            "evaluation": latest_evaluation,
            "provider": meta.get("provider"),
        },
        latency_ms=meta.get("latency_ms"),
        input_tokens=meta.get("input_tokens"),
        estimated_cost_usd=meta.get("estimated_cost_usd"),
    )


def get_status(session_id: str) -> SessionStatusResponse:
    session = store.get(session_id)
    if session is None:
        raise SessionNotFoundError(session_id)

    snapshot = compiled_graph.get_state(_config(session_id)).values
    question_set = snapshot.get("question_set")
    total_questions = len(question_set["questions"]) if question_set else 0

    return SessionStatusResponse(
        session_id=session_id,
        state=SessionState(snapshot["state"]) if snapshot.get("state") else session["state"],
        current_question_index=snapshot.get("current_question_index", 0),
        total_questions=total_questions,
    )
