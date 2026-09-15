import logging
import threading
import time

from anthropic import Anthropic
from google import genai
from google.genai import errors, types
from groq import Groq
from mistralai.client import Mistral
from openai import OpenAI

from app.config import Settings
from app.llm.token_counter import count_messages_tokens, estimate_cost_usd

logger = logging.getLogger(__name__)

PROVIDER_CLASS_TO_KEY = {
    "GroqProvider": "groq",
    "GeminiProvider": "gemini",
    "ClaudeProvider": "claude",
    "OpenAIProvider": "openai",
    "DeepSeekProvider": "deepseek",
    "OpenRouterProvider": "openrouter",
    "MistralProvider": "mistral",
}


class ClaudeProvider:
    def __init__(self, config: Settings):
        self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.model = config.ANTHROPIC_MODEL

    def complete(self, system: str, messages: list[dict]) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system,
            messages=messages,
        )
        return response.content[0].text


class GeminiProvider:
    def __init__(self, config: Settings):
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model = config.GEMINI_MODEL

    def complete(self, system: str, messages: list[dict]) -> str:
        history = [
            types.Content(
                role="model" if message["role"] == "assistant" else message["role"],
                parts=[types.Part.from_text(text=message["content"])],
            )
            for message in messages[:-1]
        ]
        try:
            chat = self.client.chats.create(
                model=self.model,
                config=types.GenerateContentConfig(system_instruction=system),
                history=history,
            )
            response = chat.send_message(messages[-1]["content"])
        except errors.ClientError as exc:
            if exc.code == 404:
                raise ValueError(
                    f"Gemini model '{self.model}' not found. Update GEMINI_MODEL in "
                    "your .env. Check available models at: "
                    "https://ai.google.dev/gemini-api/docs/models"
                ) from exc
            raise
        return response.text


class GroqProvider:
    def __init__(self, config: Settings):
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model = config.GROQ_MODEL

    def complete(self, system: str, messages: list[dict]) -> str:
        full_messages = [{"role": "system", "content": system}] + messages
        response = self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
        )
        return response.choices[0].message.content


class OpenAIProvider:
    def __init__(self, config: Settings):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_MODEL

    def complete(self, system: str, messages: list[dict]) -> str:
        full_messages = [{"role": "system", "content": system}] + messages
        response = self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
        )
        return response.choices[0].message.content


class DeepSeekProvider:
    def __init__(self, config: Settings):
        self.client = OpenAI(api_key=config.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
        self.model = config.DEEPSEEK_MODEL

    def complete(self, system: str, messages: list[dict]) -> str:
        full_messages = [{"role": "system", "content": system}] + messages
        response = self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
        )
        return response.choices[0].message.content


class OpenRouterProvider:
    def __init__(self, config: Settings):
        self.client = OpenAI(api_key=config.OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")
        self.model = config.OPENROUTER_MODEL

    def complete(self, system: str, messages: list[dict]) -> str:
        full_messages = [{"role": "system", "content": system}] + messages
        response = self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
        )
        return response.choices[0].message.content


class MistralProvider:
    def __init__(self, config: Settings):
        self.client = Mistral(api_key=config.MISTRAL_API_KEY)
        self.model = config.MISTRAL_MODEL

    def complete(self, system: str, messages: list[dict]) -> str:
        full_messages = [{"role": "system", "content": system}] + messages
        response = self.client.chat.complete(
            model=self.model,
            messages=full_messages,
        )
        return response.choices[0].message.content


_last_call_meta: dict[int, dict] = {}


def get_last_call_meta() -> dict:
    return _last_call_meta.pop(threading.get_ident(), {})


class FallbackProvider:
    def __init__(self, providers: list):
        self.providers = providers

    def complete(self, system: str, messages: list[dict]) -> str:
        last_exc: Exception | None = None
        for provider in self.providers:
            try:
                token_count = count_messages_tokens(system, messages)
                provider_key = PROVIDER_CLASS_TO_KEY.get(provider.__class__.__name__, "default")

                start = time.perf_counter()
                result = provider.complete(system, messages)
                elapsed_ms = (time.perf_counter() - start) * 1000

                _last_call_meta[threading.get_ident()] = {
                    "provider": provider.__class__.__name__,
                    "latency_ms": elapsed_ms,
                    "input_tokens": token_count,
                    "estimated_cost_usd": estimate_cost_usd(token_count, provider_key),
                }
                return result
            except Exception as exc:
                logger.warning("%s failed, trying next provider: %s", type(provider).__name__, exc)
                last_exc = exc
        raise last_exc
