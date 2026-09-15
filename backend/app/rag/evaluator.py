def compute_retrieval_precision(retrieved_chunks: list[str], evaluation: dict) -> float:
    concepts = (
        evaluation.get("correct_concepts", [])
        + evaluation.get("missing_concepts", [])
        + evaluation.get("misconceptions", [])
    )
    if not concepts or not retrieved_chunks:
        return 0.0

    lowered_chunks = [chunk.lower() for chunk in retrieved_chunks]
    found = sum(
        1 for concept in concepts if any(concept.lower() in chunk for chunk in lowered_chunks)
    )
    return found / len(concepts)


def compute_answer_faithfulness(candidate_answer: str, correct_concepts: list[str]) -> float:
    if not correct_concepts:
        return 1.0

    lowered_answer = candidate_answer.lower()
    matches = sum(1 for concept in correct_concepts if concept.lower() in lowered_answer)
    return matches / len(correct_concepts)
