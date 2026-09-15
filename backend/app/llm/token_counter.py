import tiktoken

COST_PER_MILLION_TOKENS = {
    "groq": 0.05,
    "gemini": 0.075,
    "claude": 3.0,
    "openai": 2.5,
    "deepseek": 0.14,
    "openrouter": 0.2,
    "mistral": 0.25,
    "default": 0.5,
}


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def count_messages_tokens(system: str, messages: list[dict]) -> int:
    total_text = system + "".join(message["content"] for message in messages)
    return count_tokens(total_text)


def estimate_cost_usd(token_count: int, provider: str) -> float:
    rate = COST_PER_MILLION_TOKENS.get(provider, COST_PER_MILLION_TOKENS["default"])
    return (token_count / 1_000_000) * rate
