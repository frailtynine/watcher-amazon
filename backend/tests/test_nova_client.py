"""Tests for Amazon Nova client."""
import pytest
from unittest.mock import MagicMock, patch

from app.ai.nova_client import NovaClient
from app.ai.base import ProcessingResult
from app.schemas.newspaper import NewsItemNewspaperAIResponse


def make_response(text: str, input_tokens: int = 100, output_tokens: int = 50):
    """Build a mock Bedrock converse response."""
    return {
        "output": {
            "message": {
                "content": [{"text": text}]
            }
        },
        "usage": {
            "inputTokens": input_tokens,
            "outputTokens": output_tokens,
        },
    }


def make_tool_response(payload: dict):
    """Build a mock Bedrock converse response with toolUse payload."""
    return {
        "output": {
            "message": {
                "content": [{
                    "toolUse": {
                        "name": NovaClient.NEWSPAPER_TOOL_NAME,
                        "input": payload,
                    }
                }]
            }
        },
        "usage": {
            "inputTokens": 100,
            "outputTokens": 50,
        },
    }


@pytest.fixture
def nova_client():
    """Create a NovaClient with fake credentials (no real AWS call)."""
    with patch("boto3.client"):
        client = NovaClient(
            aws_access_key_id="fake-key",
            aws_secret_access_key="fake-secret",
            region_name="us-east-1",
        )
    return client


@pytest.mark.asyncio
async def test_nova_client_initialization():
    """Test NovaClient initializes with correct defaults."""
    with patch("boto3.client"):
        client = NovaClient(
            aws_access_key_id="key",
            aws_secret_access_key="secret",
        )
    assert client.model_name == NovaClient.MODEL_ID
    assert client.MODEL_ID == "global.amazon.nova-2-lite-v1:0"


@pytest.mark.asyncio
async def test_nova_client_custom_model():
    """Test NovaClient accepts a custom model ID."""
    with patch("boto3.client"):
        client = NovaClient(
            aws_access_key_id="key",
            aws_secret_access_key="secret",
            model_id="amazon.nova-pro-v1:0",
        )
    assert client.model_name == "amazon.nova-pro-v1:0"


@pytest.mark.asyncio
async def test_process_news_positive(nova_client):
    """Test successful news processing returning a positive result."""
    response = make_response(
        '{"result": true, "thinking": "Matches the criteria"}'
    )
    nova_client.client.converse = MagicMock(return_value=response)

    result = await nova_client.process_news(
        title="AI breakthrough",
        content="Researchers achieve new milestone in AI",
        prompt="Find articles about artificial intelligence",
    )

    assert isinstance(result, ProcessingResult)
    assert result.result is True
    assert result.thinking == "Matches the criteria"
    assert result.tokens_used == 150  # 100 + 50


@pytest.mark.asyncio
async def test_process_news_negative(nova_client):
    """Test news processing returning a negative result."""
    response = make_response(
        '{"result": false, "thinking": "Unrelated topic"}',
        input_tokens=80,
        output_tokens=30,
    )
    nova_client.client.converse = MagicMock(return_value=response)

    result = await nova_client.process_news(
        title="Pasta recipe",
        content="How to make carbonara",
        prompt="Find articles about technology",
    )

    assert result.result is False
    assert result.thinking == "Unrelated topic"
    assert result.tokens_used == 110


@pytest.mark.asyncio
async def test_process_news_missing_thinking(nova_client):
    """Test that missing 'thinking' field defaults to empty string."""
    response = make_response('{"result": true}')
    nova_client.client.converse = MagicMock(return_value=response)

    result = await nova_client.process_news(
        title="Test", content="Content", prompt="Prompt"
    )

    assert result.result is True
    assert result.thinking == ""


@pytest.mark.asyncio
async def test_process_news_api_error(nova_client):
    """Test that API errors propagate correctly."""
    nova_client.client.converse = MagicMock(
        side_effect=Exception("AWS connection error")
    )

    with pytest.raises(Exception, match="AWS connection error"):
        await nova_client.process_news(
            title="Test", content="Content", prompt="Prompt"
        )


@pytest.mark.asyncio
async def test_extract_tokens_no_usage(nova_client):
    """Test token extraction when usage field is absent."""
    response = {
        "output": {"message": {"content": [{"text": "{}"}]}},
    }
    assert nova_client._extract_tokens(response) == 0


@pytest.mark.asyncio
async def test_extract_text(nova_client):
    """Test text extraction from Bedrock response."""
    response = make_response('{"result": false, "thinking": "ok"}')
    text = nova_client._extract_text(response)
    assert text == '{"result": false, "thinking": "ok"}'


@pytest.mark.asyncio
async def test_converse_called_with_correct_args(nova_client):
    """Test that converse is called with the right structure."""
    response = make_response('{"result": true, "thinking": "yes"}')
    nova_client.client.converse = MagicMock(return_value=response)

    await nova_client.process_news(
        title="Headline",
        content="Body text",
        prompt="Find tech news",
    )

    call_kwargs = nova_client.client.converse.call_args.kwargs
    assert call_kwargs["modelId"] == NovaClient.MODEL_ID
    assert len(call_kwargs["system"]) == 1
    assert "Find tech news" in call_kwargs["system"][0]["text"]
    assert call_kwargs["messages"][0]["role"] == "user"
    assert "Headline" in call_kwargs["messages"][0]["content"][0]["text"]


@pytest.mark.asyncio
async def test_process_newspaper(nova_client):
    """Test process_newspaper returns validated structured payload."""
    payload = {
        "new_item_title": "Headline",
        "new_item_summary": "Summary",
        "new_item_position": [0, 0],
        "updates": [],
    }
    response = make_tool_response(payload)
    nova_client.client.converse = MagicMock(return_value=response)

    result = await nova_client.process_newspaper("some newspaper prompt")

    assert isinstance(result, NewsItemNewspaperAIResponse)
    assert result.new_item_title == "Headline"
    assert list(result.new_item_position) == [0, 0]
