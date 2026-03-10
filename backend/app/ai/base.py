"""Base AI client for news processing."""
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of processing a news item."""
    result: bool
    thinking: str
    tokens_used: int


class BaseAIClient(ABC):
    """Abstract base class for AI clients."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.logger = logger.getChild(self.__class__.__name__)

    async def process_news(
        self,
        title: str,
        content: str,
        prompt: str,
    ) -> ProcessingResult:
        """Process a news item against a prompt.

        Args:
            title: News item title
            content: News item content
            prompt: User-defined filtering prompt

        Returns:
            ProcessingResult with analysis outcome
        """
        system_instruction = self._build_system_instruction(prompt)
        user_message = self._build_user_message(title, content)
        response_text, tokens_used = await self._generate(
            system_instruction, user_message
        )
        result_data = self._parse_json_object(response_text)
        return ProcessingResult(
            result=result_data.get("result", False),
            thinking=result_data.get("thinking", ""),
            tokens_used=tokens_used,
        )

    @abstractmethod
    async def _generate(
        self, system_instruction: str, user_message: str
    ) -> tuple[str, int]:
        """Call the underlying AI API.

        Args:
            system_instruction: System-level instruction
            user_message: User message with news content

        Returns:
            Tuple of (response_text, tokens_used)
        """
        ...

    def _build_system_instruction(self, user_prompt: str) -> str:
        return (
            f"You are a news monitoring assistant. "
            f"Your task is to analyze news articles and determine "
            f"if they match the following news filter:\n\n{user_prompt}\n\n"
            f"Respond with a raw JSON object only — no markdown, "
            f"no code fences, no explanations:\n"
            f'{{"result": <true|false>, "thinking": "<explanation>"}}'
        )

    def _build_user_message(self, title: str, content: str) -> str:
        return f"Title: {title}\n\nContent: {content}"

    def _parse_json_object(self, response_text: str) -> dict:
        """Parse first JSON object from model output safely."""
        decoder = json.JSONDecoder()
        start = response_text.find("{")
        if start < 0:
            raise json.JSONDecodeError("No JSON object found", response_text, 0)
        parsed, _ = decoder.raw_decode(response_text[start:])
        if not isinstance(parsed, dict):
            raise json.JSONDecodeError(
                "Expected JSON object at top level",
                response_text,
                start,
            )
        return parsed
