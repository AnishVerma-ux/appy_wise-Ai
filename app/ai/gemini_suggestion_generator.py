import logging
from typing import Protocol

from google import genai
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.suggestion import SuggestionContent


logger = logging.getLogger(__name__)


class SuggestionProviderError(Exception):
    """Raised when the AI provider cannot generate a result."""


class SuggestionProviderNotConfiguredError(
    SuggestionProviderError
):
    """Raised when the Gemini API key is missing."""


class SuggestionGenerator(Protocol):
    model: str
    provider: str

    def generate(
        self,
        prompt: str,
    ) -> SuggestionContent:
        ...


class GeminiSuggestionGenerator:
    provider = "gemini"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        configured_key = api_key

        if (
            configured_key is None
            and settings.gemini_api_key is not None
        ):
            configured_key = (
                settings.gemini_api_key.get_secret_value()
            )

        self.api_key = configured_key
        self.model = model or settings.gemini_model

    def generate(
        self,
        prompt: str,
    ) -> SuggestionContent:
        if not self.api_key:
            raise SuggestionProviderNotConfiguredError(
                "Gemini API key is not configured"
            )

        try:
            client = genai.Client(
                api_key=self.api_key
            )

            interaction = client.interactions.create(
                model=self.model,
                input=prompt,
                store=False,
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": (
                        SuggestionContent.model_json_schema()
                    ),
                },
            )

        except Exception as exc:
            logger.exception(
                "Gemini suggestion request failed"
            )

            raise SuggestionProviderError(
                "AI suggestion service is unavailable"
            ) from exc

        if not interaction.output_text:
            raise SuggestionProviderError(
                "AI suggestion service returned an empty response"
            )

        try:
            return SuggestionContent.model_validate_json(
                interaction.output_text
            )

        except ValidationError as exc:
            logger.exception(
                "Gemini returned invalid structured output"
            )

            raise SuggestionProviderError(
                "AI suggestion service returned an invalid response"
            ) from exc