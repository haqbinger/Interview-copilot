import logging

logger = logging.getLogger(__name__)

_providers: dict[str, object] = {}


def register(session_id: str, provider) -> None:
    _providers[session_id] = provider


def get(session_id: str):
    return _providers.get(session_id)


def unregister(session_id: str) -> None:
    _providers.pop(session_id, None)
