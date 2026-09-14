import logging

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


class SessionNotFoundError(Exception):
    pass


def _config(session_id: str) -> dict:
    return {"configurable": {"thread_id": session_id}}


def start_session(session_id: str, github_url: str, mode: InterviewMode, provider) -> SessionResponse:
    register_provider(session_id, provider)
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
    }
    compiled_graph.invoke(initial_state, _config(session_id))
    result = compiled_graph.get_state(_config(session_id)).values

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
        },
    )


def submit_explanation(session_id: str, explanation: str, provider) -> SessionResponse:
    register_provider(session_id, provider)
    config = _config(session_id)
    compiled_graph.update_state(config, {"current_input": explanation})
    compiled_graph.invoke(None, config)
    result = compiled_graph.get_state(_config(session_id)).values

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
        data={"question": result["current_question"]},
    )


def submit_answer(session_id: str, answer: str, provider) -> SessionResponse:
    register_provider(session_id, provider)
    config = _config(session_id)
    compiled_graph.update_state(config, {"current_input": answer})
    compiled_graph.invoke(None, config)
    result = compiled_graph.get_state(_config(session_id)).values

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
            data={"report": result["report"], "evaluation": latest_evaluation},
        )

    return SessionResponse(
        session_id=session_id,
        state=SessionState(result["state"]),
        message="Next question ready.",
        data={"question": result["current_question"], "evaluation": latest_evaluation},
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
