"""T042: `GeminiLLMClient` — implementação de `LLMClient` com a API do
Google Gemini, na camada paga (decisão O1 do plan.md). Usa o SDK oficial
`google-genai`.
"""

from __future__ import annotations

from collections.abc import Iterator

from app.core.config import Settings
from app.llm.base import LLMChunk, LLMClient, LLMUnavailable, Message, Usage
from app.observability.logging import get_logger

logger = get_logger(__name__)


class GeminiLLMClient(LLMClient):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        from google import genai

        self._client = genai.Client(api_key=settings.gemini_api_key)

    def stream(
        self,
        *,
        system: str,
        messages: list[Message],
        temperature: float,
        max_output_tokens: int,
    ) -> Iterator[LLMChunk]:
        from google.genai import types

        contents = [
            types.Content(
                role="user" if m.role == "user" else "model",
                parts=[types.Part.from_text(text=m.content)],
            )
            for m in messages
        ]

        try:
            stream = self._client.models.generate_content_stream(
                model=self._settings.gemini_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                ),
            )
            last_usage: Usage | None = None
            for chunk in stream:
                text = chunk.text or ""
                usage_meta = getattr(chunk, "usage_metadata", None)
                if usage_meta is not None:
                    last_usage = Usage(
                        input_tokens=getattr(usage_meta, "prompt_token_count", 0) or 0,
                        output_tokens=getattr(usage_meta, "candidates_token_count", 0) or 0,
                    )
                if text:
                    yield LLMChunk(text=text)
            yield LLMChunk(text="", usage=last_usage)
        except Exception as exc:  # noqa: BLE001
            logger.exception("llm.gemini_stream_failed")
            raise LLMUnavailable(str(exc)) from exc

    def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            result = self._client.models.embed_content(
                model=self._settings.gemini_embedding_model,
                contents=texts,
            )
            return [embedding.values for embedding in result.embeddings]
        except Exception as exc:  # noqa: BLE001
            logger.exception("llm.gemini_embed_failed")
            raise LLMUnavailable(str(exc)) from exc
