import logging
import uuid
from datetime import datetime, timezone

from app.models.schemas import InterviewMode, SessionState

logger = logging.getLogger(__name__)


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, dict] = {}

    def create(self, mode: InterviewMode) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {
            "session_id": session_id,
            "state": SessionState.INGESTING,
            "mode": mode,
            "repo_summary": None,
            "briefing": None,
            "candidate_explanation": None,
            "question_set": None,
            "current_question_index": 0,
            "evaluations": [],
            "report": None,
            "created_at": datetime.now(timezone.utc),
        }
        return session_id

    def get(self, session_id: str) -> dict | None:
        return self._sessions.get(session_id)

    def update(self, session_id: str, **kwargs) -> None:
        session = self._sessions.get(session_id)
        if session is None:
            return
        session.update(kwargs)

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


store = SessionStore()
