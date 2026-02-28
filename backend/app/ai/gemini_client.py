"""Gemini API client for news processing."""
import json
import logging
from dataclasses import dataclass

import google.genai as genai
from google.genai import types

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of processing a news item."""
    result: bool
    thinking: str
    tokens_used: int


class GeminiClient:
    """Client for interacting with Gemini API."""

    MODEL_NAME = "gemini-2.5-flash-lite"

    def __init__(self, api_key: str, model_name: str = MODEL_NAME):
        """Initialize Gemini client with API key.

        Args:
            api_key: Google API key for Gemini
            model_name: Name of the Gemini model to use
        """
        self.model_name = model_name
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)

    async def process_newspaper(
        self
    ) -> None:
        """Placeholder for processing newspaper items."""
        pass

    async def process_news(
        self,
        title: str,
        content: str,
        prompt: str
    ) -> ProcessingResult:
        """Process news item against a prompt using Gemini.

        Args:
            title: News item title
            content: News item content
            prompt: User-defined prompt for filtering

        Returns:
            ProcessingResult with analysis outcome

        Raises:
            Exception: If API call fails
        """
        system_instruction = self._build_system_instruction(prompt)
        user_message = self._build_user_message(title, content)

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema={
                    "type": "object",
                    "properties": {
                        "result": {"type": "boolean"},
                        "thinking": {"type": "string"}
                    },
                    "required": ["result", "thinking"]
                }
            )
        )

        # Parse response
        result_text = response.text
        result_data = json.loads(result_text)
        tokens_used = self._count_tokens(response)

        return ProcessingResult(
            result=result_data.get("result", False),
            thinking=result_data.get("thinking", ""),
            tokens_used=tokens_used
        )

    def _build_system_instruction(self, user_prompt: str) -> str:
        """Build system instruction for Gemini.

        Args:
            user_prompt: User-defined filtering prompt

        Returns:
            Complete system instruction
        """
        return (
            f"You are a news monitoring assistant. "
            f"Your task is to analyze news articles and determine "
            f"if they match the following news filter:\n\n{user_prompt}\n\n"
            f"Return a JSON object with:\n"
            f"- 'result': true if the news matches the filter, "
            f"false otherwise\n"
            f"- 'thinking': brief explanation of your decision"
        )

    def _build_user_message(self, title: str, content: str) -> str:
        """Build user message with news content.

        Args:
            title: News title
            content: News content

        Returns:
            Formatted message
        """
        return f"Title: {title}\n\nContent: {content}"

    def _count_tokens(self, response) -> int:
        """Count tokens used in the response.

        Args:
            response: Gemini API response

        Returns:
            Total token count
        """
        usage_metadata = response.usage_metadata
        if not usage_metadata:
            return 0

        return (
            usage_metadata.prompt_token_count +
            usage_metadata.candidates_token_count
        )
