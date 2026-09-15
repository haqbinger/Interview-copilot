import json
import re

MAX_SANITIZED_LENGTH = 2000

CODE_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)
SCRIPT_TAG_PATTERN = re.compile(r"<script\b[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)
MARKDOWN_BREAKING_PATTERN = re.compile(r"[`*_#\[\]]")


def validate_llm_json(response_text: str, required_keys: list[str]) -> dict:
    stripped = CODE_FENCE_PATTERN.sub("", response_text.strip()).strip()

    try:
        data = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM returned invalid JSON") from exc

    missing = [key for key in required_keys if key not in data]
    if missing:
        raise ValueError(f"LLM response missing required fields: {missing}")

    return data


def sanitize_llm_text(text: str) -> str:
    cleaned = SCRIPT_TAG_PATTERN.sub("", text)
    cleaned = MARKDOWN_BREAKING_PATTERN.sub("", cleaned)
    return cleaned[:MAX_SANITIZED_LENGTH]
