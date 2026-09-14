import logging

from anthropic import Anthropic
from google import genai
from google.genai import errors, types
from groq import Groq

from app.config import Settings

logger = logging.getLogger(__name__)


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


class FallbackProvider:
    def __init__(self, providers: list):
        self.providers = providers

    def complete(self, system: str, messages: list[dict]) -> str:
        last_exc: Exception | None = None
        for provider in self.providers:
            try:
                return provider.complete(system, messages)
            except Exception as exc:
                logger.warning("%s failed, trying next provider: %s", type(provider).__name__, exc)
                last_exc = exc
        raise last_exc
