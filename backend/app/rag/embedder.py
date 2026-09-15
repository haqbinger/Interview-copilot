import logging

import chromadb
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

CHUNK_THRESHOLD = 1000
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
MAX_INDEXED_CHUNK_CHARS = 300

_model = SentenceTransformer("all-MiniLM-L6-v2")
_client = chromadb.Client()


class RepoEmbedder:
    def build_index(self, session_id: str, file_contents: dict[str, str]) -> None:
        collection = _client.get_or_create_collection(name=session_id, embedding_function=None)

        documents = []
        metadatas = []
        ids = []
        for path, content in file_contents.items():
            for chunk_index, chunk in enumerate(_chunk_text(content)):
                documents.append(chunk[:MAX_INDEXED_CHUNK_CHARS])
                metadatas.append({"path": path, "chunk": chunk_index})
                ids.append(f"{path}::{chunk_index}")

        if not documents:
            return

        embeddings = _model.encode(documents).tolist()
        collection.add(documents=documents, embeddings=embeddings, metadatas=metadatas, ids=ids)

    def retrieve(self, session_id: str, query: str, k: int = 2) -> list[str]:
        collection = _client.get_or_create_collection(name=session_id, embedding_function=None)
        if collection.count() == 0:
            return []

        query_embedding = _model.encode([query]).tolist()
        results = collection.query(query_embeddings=query_embedding, n_results=k)

        documents = results.get("documents") or [[]]
        metadatas = results.get("metadatas") or [[]]

        return [
            f"### {metadata['path']}\n{document}"
            for document, metadata in zip(documents[0], metadatas[0])
        ]

    def delete_index(self, session_id: str) -> None:
        try:
            _client.delete_collection(name=session_id)
        except Exception as exc:
            logger.warning("Failed to delete RAG index for session %s: %s", session_id, exc)


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
