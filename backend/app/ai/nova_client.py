"""Amazon Nova client for news processing via AWS Bedrock."""
import asyncio
import logging
from typing import Optional

import boto3

from app.ai.base import BaseAIClient

logger = logging.getLogger(__name__)


class NovaClient(BaseAIClient):
    """Client for interacting with Amazon Nova via AWS Bedrock."""

    MODEL_ID = "amazon.nova-lite-v1:0"

    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region_name: str = "us-east-1",
        model_id: str = MODEL_ID,
    ):
        """Initialize Nova client with AWS credentials.

        Args:
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            region_name: AWS region where Bedrock is available
            model_id: Bedrock model ID for Amazon Nova
        """
        super().__init__(model_id)
        self.client = boto3.client(
            "bedrock-runtime",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )

    async def _generate(
        self,
        system_instruction: str,
        user_message: str,
    ) -> tuple[str, int]:
        """Call Bedrock converse API and return (response_text, tokens_used).

        Args:
            system_instruction: System-level instruction
            user_message: User message with news content

        Returns:
            Tuple of (response_text, tokens_used)
        """
        response = await asyncio.to_thread(
            self.client.converse,
            modelId=self.model_name,
            system=[{"text": system_instruction}],
            messages=[
                {
                    "role": "user",
                    "content": [{"text": user_message}],
                }
            ],
            inferenceConfig={
                "maxTokens": 1024,
                "temperature": 0.1,
            },
        )

        response_text = self._extract_text(response)
        tokens_used = self._extract_tokens(response)
        cleaned = self._clean_json(response_text)
        self.logger.debug("Raw Bedrock response: %r → cleaned: %r", response_text, cleaned)
        return cleaned, tokens_used

    def _clean_json(self, text: str) -> str:
        """Strip markdown code fences from model output if present."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            # drop opening fence (```json or ```) and closing fence
            inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
            text = "\n".join(inner).strip()
        return text

    def _extract_text(self, response: dict) -> str:
        """Extract text content from Bedrock converse response.

        Args:
            response: Raw Bedrock API response

        Returns:
            Text content from the response
        """
        return response["output"]["message"]["content"][0]["text"]

    async def process_newspaper(self, prompt: str) -> str:
        """Process newspaper layout and return JSON string.

        Args:
            prompt: Full newspaper processing prompt with current layout

        Returns:
            JSON string with newspaper layout updates
        """
        text, _ = await self._generate(
            system_instruction=(
                "You must respond with valid JSON only. "
                "No markdown, no explanations, no code fences."
            ),
            user_message=prompt,
        )
        return text

    def _extract_tokens(self, response: dict) -> int:
        """Extract total token count from Bedrock converse response.

        Args:
            response: Raw Bedrock API response

        Returns:
            Total tokens used (input + output)
        """
        usage: Optional[dict] = response.get("usage")
        if not usage:
            return 0
        return usage.get("inputTokens", 0) + usage.get("outputTokens", 0)
