import re

GITHUB_URL_PATTERN = re.compile(r"^https://github\.com/([\w-]+)/([\w-]+)$")
MAX_GITHUB_URL_LENGTH = 200
MAX_ANSWER_LENGTH = 5000

PROMPT_INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all instructions",
    "disregard your",
    "you are now",
    "new instruction:",
    "system prompt",
    "forget your instructions",
    "jailbreak",
]

API_KEY_PREFIXES = {
    "groq": ("gsk_",),
    "openai": ("sk-",),
    "claude": ("sk-ant-",),
    "gemini": ("AQ.", "AIza"),
    "deepseek": ("sk-",),
    "openrouter": ("sk-or-",),
}


def validate_github_url(url: str) -> str:
    if len(url) > MAX_GITHUB_URL_LENGTH:
        raise ValueError(f"GitHub URL exceeds max length of {MAX_GITHUB_URL_LENGTH} chars")
    if not GITHUB_URL_PATTERN.match(url):
        raise ValueError("Invalid GitHub URL: must be https://github.com/<owner>/<repo>")
    return url


def validate_answer(text: str) -> str:
    cleaned = text.strip()
    if len(cleaned) > MAX_ANSWER_LENGTH:
        cleaned = cleaned[:MAX_ANSWER_LENGTH]

    lowered = cleaned.lower()
    for pattern in PROMPT_INJECTION_PATTERNS:
        if pattern in lowered:
            raise ValueError("Answer contains disallowed content")
    return cleaned


def validate_api_key(provider: str, key: str) -> str:
    cleaned = key.strip()
    if provider == "mistral":
        if not cleaned:
            raise ValueError("Invalid mistral API key format")
        return cleaned

    prefixes = API_KEY_PREFIXES.get(provider)
    if prefixes is None:
        raise ValueError(f"Invalid {provider} API key format")
    if not cleaned.startswith(prefixes):
        raise ValueError(f"Invalid {provider} API key format")
    return cleaned
