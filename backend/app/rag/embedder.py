import logging

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

CHUNK_THRESHOLD = 1000
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
MAX_INDEXED_CHUNK_CHARS = 300

_indexes: dict[str, dict] = {}


class RepoEmbedder:
    def build_index(self, session_id: str, file_contents: dict[str, str]) -> None:
        chunks = []
        paths = []
        for path, content in file_contents.items():
            for chunk in _chunk_text(content):
                chunks.append(chunk[:MAX_INDEXED_CHUNK_CHARS])
                paths.append(path)

        if not chunks:
            return

        vectorizer = TfidfVectorizer()
        matrix = vectorizer.fit_transform(chunks)
        _indexes[session_id] = {
            "vectorizer": vectorizer,
            "matrix": matrix,
            "chunks": chunks,
            "paths": paths,
        }

    def retrieve(self, session_id: str, query: str, k: int = 2) -> list[str]:
        index = _indexes.get(session_id)
        if not index:
            return []

        query_vector = index["vectorizer"].transform([query])
        similarities = cosine_similarity(query_vector, index["matrix"])[0]
        top_indices = similarities.argsort()[::-1][:k]

        return [
            f"### {index['paths'][i]}\n{index['chunks'][i]}"
            for i in top_indices
        ]

    def delete_index(self, session_id: str) -> None:
        _indexes.pop(session_id, None)


def _chunk_text(content: str) -> list[str]:
    if len(content) <= CHUNK_THRESHOLD:
        return [content]

    chunks = []
    step = CHUNK_SIZE - CHUNK_OVERLAP
    for start in range(0, len(content), step):
        chunk = content[start : start + CHUNK_SIZE]
        if chunk:
            chunks.append(chunk)
    return chunks
