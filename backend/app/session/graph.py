import logging
from typing import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.ingestion.briefing_generator import generate_briefing
from app.ingestion.ingest_service import fetch_repo_summary
from app.interview.answer_evaluator import evaluate_answer
from app.interview.question_generator import generate_questions
from app.interview.report_generator import generate_report
from app.models.schemas import (
    AnswerSubmission,
    BriefingResult,
    GenerateQuestionsRequest,
    GenerateReportRequest,
    InterviewMode,
    Question,
    RepoSummary,
    SessionState,
)
from app.session.provider_registry import get as get_provider

logger = logging.getLogger(__name__)


class InterviewState(TypedDict):
    session_id: str
    state: str
    mode: str
    github_url: str
    repo_summary: dict | None
    briefing: dict | None
    candidate_explanation: str | None
    question_set: dict | None
    current_question_index: int
    current_question: dict | None
    evaluations: list[dict]
    report: dict | None
    current_input: str | None


def ingest_node(state: InterviewState) -> dict:
    provider = get_provider(state["session_id"])
    repo_summary = fetch_repo_summary(state["github_url"])
    briefing = generate_briefing(repo_summary, provider)
    return {
        "repo_summary": repo_summary.model_dump(mode="json"),
        "briefing": briefing.model_dump(mode="json"),
        "state": SessionState.EXPLAINING.value,
    }


def explain_node(state: InterviewState) -> dict:
    provider = get_provider(state["session_id"])
    candidate_explanation = state["current_input"]

    request = GenerateQuestionsRequest(
        repo_summary=RepoSummary(**state["repo_summary"]),
        briefing=BriefingResult(**state["briefing"]),
        candidate_explanation=candidate_explanation,
        mode=InterviewMode(state["mode"]),
    )
    response = generate_questions(request, provider)

    return {
        "candidate_explanation": candidate_explanation,
        "question_set": response.question_set.model_dump(mode="json"),
        "current_question_index": 0,
        "state": SessionState.INTERVIEWING.value,
        "current_input": None,
    }


def interview_node(state: InterviewState) -> dict:
    questions = state["question_set"]["questions"]
    index = state["current_question_index"]
    current_question = questions[index] if index < len(questions) else None

    return {
        "current_question": current_question,
        "state": SessionState.INTERVIEWING.value,
    }


def evaluate_node(state: InterviewState) -> dict:
    provider = get_provider(state["session_id"])
    current_question = Question(**state["current_question"])

    submission = AnswerSubmission(
        session_id=state["session_id"],
        question_id=current_question.id,
        question_text=current_question.text,
        candidate_answer=state["current_input"],
        repo_summary=RepoSummary(**state["repo_summary"]),
        category=current_question.category,
    )
    result = evaluate_answer(submission, provider)

    evaluations = state["evaluations"] + [result.evaluation.model_dump(mode="json")]
    next_index = state["current_question_index"] + 1
    total_questions = len(state["question_set"]["questions"])
    next_state = (
        SessionState.REPORTING.value if next_index >= total_questions else SessionState.INTERVIEWING.value
    )

    return {
        "evaluations": evaluations,
        "current_question_index": next_index,
        "state": next_state,
        "current_input": None,
    }


def report_node(state: InterviewState) -> dict:
    provider = get_provider(state["session_id"])

    request = GenerateReportRequest(
        session_id=state["session_id"],
        mode=InterviewMode(state["mode"]),
        repo_summary=RepoSummary(**state["repo_summary"]),
        briefing=BriefingResult(**state["briefing"]),
        evaluations=state["evaluations"],
    )
    report = generate_report(request, provider)

    return {"report": report.model_dump(mode="json"), "state": SessionState.COMPLETE.value}


def _route_after_evaluate(state: InterviewState) -> str:
    return "done" if state["state"] == SessionState.REPORTING.value else "continue"


def _build_graph():
    graph = StateGraph(InterviewState)
    graph.add_node("ingest_node", ingest_node)
    graph.add_node("explain_node", explain_node)
    graph.add_node("interview_node", interview_node)
    graph.add_node("evaluate_node", evaluate_node)
    graph.add_node("report_node", report_node)

    graph.add_edge(START, "ingest_node")
    graph.add_edge("ingest_node", "explain_node")
    graph.add_edge("explain_node", "interview_node")
    graph.add_edge("interview_node", "evaluate_node")
    graph.add_conditional_edges(
        "evaluate_node",
        _route_after_evaluate,
        {"continue": "interview_node", "done": "report_node"},
    )
    graph.add_edge("report_node", END)

    return graph.compile(
        checkpointer=MemorySaver(),
        interrupt_before=["explain_node", "evaluate_node"],
    )


compiled_graph = _build_graph()
