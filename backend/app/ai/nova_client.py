"""Amazon Nova client for news processing via AWS Bedrock."""
import asyncio
import json
import logging
from typing import Any, Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from pydantic import ValidationError

from app.ai.base import BaseAIClient
from app.schemas.newspaper import NewsItemNewspaperAIResponse

logger = logging.getLogger(__name__)


class NovaClient(BaseAIClient):
    """Client for interacting with Amazon Nova via AWS Bedrock."""

    MODEL_ID = "global.amazon.nova-2-lite-v1:0"
    NEWSPAPER_TOOL_NAME = "update_newspaper_layout"
    NEWSPAPER_TOOL_SCHEMA = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "new_item_title",
            "new_item_summary",
            "new_item_position",
            "updates",
        ],
        "properties": {
            "new_item_title": {"type": "string"},
            "new_item_summary": {"type": "string"},
            "new_item_position": {
                "type": "array",
                "items": {"type": "integer"},
                "minItems": 2,
                "maxItems": 2,
            },
            "updates": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["row_index", "position"],
                    "properties": {
                        "row_index": {"type": "integer"},
                        "position": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "minItems": 2,
                            "maxItems": 2,
                        },
                    },
                },
            },
        },
    }

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
            config=Config(max_pool_connections=50),
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
                "maxTokens": 1500,
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

    async def process_newspaper(
        self,
        prompt: str,
    ) -> NewsItemNewspaperAIResponse:
        """Process newspaper layout using tool-based structured output.

        Args:
            prompt: Full newspaper processing prompt with current layout

        Returns:
            Parsed newspaper layout updates
        """
        response = await self._converse_newspaper(prompt)
        try:
            return self._parse_newspaper_response(response)
        except (ValidationError, ClientError) as first_error:
            self.logger.warning(
                "Invalid newspaper tool response, retrying once: %s",
                first_error,
            )
            retry_prompt = (
                f"{prompt}\n\n"
                "IMPORTANT: Use tool output only and include ALL required fields:\n"
                "- new_item_title\n"
                "- new_item_summary\n"
                "- new_item_position [row,col]\n"
                "- updates (array)\n"
                "Never omit required fields."
            )
            retry_response = await self._converse_newspaper(retry_prompt)
            return self._parse_newspaper_response(retry_response)

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

    def _extract_tool_input(self, response: dict) -> dict[str, Any] | None:
        """Extract tool input payload from Bedrock converse response."""
        content = response.get("output", {}).get("message", {}).get("content", [])
        for block in content:
            tool_use = block.get("toolUse")
            if not tool_use:
                continue
            if tool_use.get("name") != self.NEWSPAPER_TOOL_NAME:
                continue

            payload = tool_use.get("input")
            if isinstance(payload, dict):
                return payload
            if isinstance(payload, str):
                try:
                    return json.loads(payload)
                except json.JSONDecodeError:
                    self.logger.error(
                        "Invalid JSON in tool payload: %r",
                        payload,
                    )
                    raise
        return None

    async def _converse_newspaper(self, prompt: str) -> dict[str, Any]:
        """Call Bedrock with tool-based schema for newspaper updates."""
        return await asyncio.to_thread(
            self.client.converse,
            modelId=self.model_name,
            system=[
                {
                    "text": (
                        "You are a news editor assistant. "
                        "Always call the provided tool and fill all required "
                        "fields in its input schema. Never answer with plain text."
                    )
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": [{"text": prompt}],
                }
            ],
            inferenceConfig={
                "maxTokens": 1500,
                "temperature": 0.1,
            },
            toolConfig={
                "tools": [
                    {
                        "toolSpec": {
                            "name": self.NEWSPAPER_TOOL_NAME,
                            "description": (
                                "Return structured updates for newspaper layout"
                            ),
                            "inputSchema": {
                                "json": self.NEWSPAPER_TOOL_SCHEMA
                            },
                        }
                    }
                ],
                "toolChoice": {
                    "tool": {"name": self.NEWSPAPER_TOOL_NAME}
                },
            },
        )

    def _parse_newspaper_response(
        self,
        response: dict[str, Any],
    ) -> NewsItemNewspaperAIResponse:
        """Parse and validate newspaper response from tool output only."""
        tool_input = self._extract_tool_input(response)
        if tool_input is None:
            raise ValueError(
                "No toolUse payload returned by model for structured output."
            )
        return NewsItemNewspaperAIResponse.model_validate(tool_input)
