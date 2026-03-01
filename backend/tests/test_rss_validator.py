"""Tests for RSS feed validation."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.validators.rss import validate_rss_feed


@pytest.fixture
def mock_valid_feed():
    """Mock a valid RSS feed."""
    return {
        "bozo": False,
        "feed": {
            "title": "Test RSS Feed",
            "subtitle": "A test feed",
        },
        "entries": [
            {
                "title": "Test Article 1",
                "link": "https://example.com/article1",
                "description": "This is test article 1",
                "published": "Mon, 15 Jan 2024 10:00:00 GMT",
            },
            {
                "title": "Test Article 2",
                "link": "https://example.com/article2",
                "description": "This is test article 2",
                "published": "Mon, 15 Jan 2024 11:00:00 GMT",
            },
        ],
    }

@pytest.fixture
def mock_feed_no_entries():
    """Mock an RSS feed with no entries."""
    return {
        "bozo": False,
        "feed": {
            "title": "Empty Feed",
        },
        "entries": [],
    }


@pytest.fixture
def mock_feed_invalid_entries():
    """Mock an RSS feed with invalid entries (missing required fields)."""
    return {
        "bozo": False,
        "feed": {
            "title": "Invalid Entries Feed",
        },
        "entries": [
            {
                "title": "Article without link",
                "description": "Description here",
            },
            {
                "link": "https://example.com/article",
                "description": "Article without title",
            },
            {
                "title": "Article without description",
                "link": "https://example.com/article",
            },
        ],
    }


@pytest.fixture
def mock_bozo_feed():
    """Mock a feed with parsing errors."""
    return {
        "bozo": True,
        "bozo_exception": Exception("Malformed XML"),
        "feed": {},
        "entries": [],
    }


@pytest.mark.asyncio
async def test_validate_rss_feed_success(mock_valid_feed):
    """Test successful RSS feed validation."""
    with patch("aiohttp.ClientSession") as mock_session:
        # Mock the HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"<rss></rss>")

        mock_session_instance = MagicMock()
        mock_session_instance.__aenter__ = AsyncMock(
            return_value=mock_session_instance
        )
        mock_session_instance.__aexit__ = AsyncMock()
        mock_session_instance.get = MagicMock()
        mock_session_instance.get.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_session_instance.get.return_value.__aexit__ = AsyncMock()

        mock_session.return_value = mock_session_instance

        # Mock feedparser
        with patch("feedparser.parse", return_value=mock_valid_feed):
            result = await validate_rss_feed("https://example.com/feed.xml")
            print(result)

    assert result["valid"] is True
    assert result["url"] == "https://example.com/feed.xml"
    assert result["title"] == "Test RSS Feed"
    assert result["error"] is None


@pytest.mark.asyncio
async def test_validate_rss_feed_empty_url():
    """Test validation with empty URL."""
    result = await validate_rss_feed("")

    assert result["valid"] is False
    assert result["error"] == "URL cannot be empty"


@pytest.mark.asyncio
async def test_validate_rss_feed_invalid_protocol():
    """Test validation with invalid URL protocol."""
    result = await validate_rss_feed("ftp://example.com/feed.xml")

    assert result["valid"] is False
    assert result["error"] == "URL must start with http:// or https://"


@pytest.mark.asyncio
async def test_validate_rss_feed_http_error():
    """Test validation with HTTP error."""
    with patch("aiohttp.ClientSession") as mock_session:
        # Mock 404 response
        mock_response = AsyncMock()
        mock_response.status = 404

        mock_session_instance = MagicMock()
        mock_session_instance.__aenter__ = AsyncMock(
            return_value=mock_session_instance
        )
        mock_session_instance.__aexit__ = AsyncMock()
        mock_session_instance.get = MagicMock()
        mock_session_instance.get.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_session_instance.get.return_value.__aexit__ = AsyncMock()

        mock_session.return_value = mock_session_instance

        result = await validate_rss_feed("https://example.com/feed.xml")

    assert result["valid"] is False
    assert "HTTP error: status code 404" in result["error"]


@pytest.mark.asyncio
async def test_validate_rss_feed_timeout():
    """Test validation with timeout."""
    import asyncio

    with patch("aiohttp.ClientSession") as mock_session:
        mock_session_instance = MagicMock()
        mock_session_instance.__aenter__ = AsyncMock(
            return_value=mock_session_instance
        )
        mock_session_instance.__aexit__ = AsyncMock()
        mock_session_instance.get = MagicMock()
        mock_session_instance.get.return_value.__aenter__ = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )

        mock_session.return_value = mock_session_instance

        result = await validate_rss_feed("https://example.com/feed.xml")

    assert result["valid"] is False
    assert "timeout" in result["error"].lower()


@pytest.mark.asyncio
async def test_validate_rss_feed_no_entries(mock_feed_no_entries):
    """Test validation with feed that has no entries."""
    with patch("aiohttp.ClientSession") as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"<rss></rss>")

        mock_session_instance = MagicMock()
        mock_session_instance.__aenter__ = AsyncMock(
            return_value=mock_session_instance
        )
        mock_session_instance.__aexit__ = AsyncMock()
        mock_session_instance.get = MagicMock()
        mock_session_instance.get.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_session_instance.get.return_value.__aexit__ = AsyncMock()

        mock_session.return_value = mock_session_instance

        with patch("feedparser.parse", return_value=mock_feed_no_entries):
            result = await validate_rss_feed("https://example.com/feed.xml")

    assert result["valid"] is False
    assert result["error"] == "Feed has no entries"


@pytest.mark.asyncio
async def test_validate_rss_feed_invalid_entries(mock_feed_invalid_entries):
    """Test validation with feed that has invalid entries."""
    with patch("aiohttp.ClientSession") as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"<rss></rss>")

        mock_session_instance = MagicMock()
        mock_session_instance.__aenter__ = AsyncMock(
            return_value=mock_session_instance
        )
        mock_session_instance.__aexit__ = AsyncMock()
        mock_session_instance.get = MagicMock()
        mock_session_instance.get.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_session_instance.get.return_value.__aexit__ = AsyncMock()

        mock_session.return_value = mock_session_instance

        with patch(
            "feedparser.parse",
            return_value=mock_feed_invalid_entries
        ):
            result = await validate_rss_feed("https://example.com/feed.xml")

    assert result["valid"] is False
    assert "missing required fields" in result["error"]


@pytest.mark.asyncio
async def test_validate_rss_feed_bozo_with_entries(mock_valid_feed):
    """Test validation with bozo feed that still has valid entries."""
    # Set bozo flag but keep valid entries
    bozo_feed = mock_valid_feed.copy()
    bozo_feed["bozo"] = True
    bozo_feed["bozo_exception"] = Exception("Minor parsing issue")

    with patch("aiohttp.ClientSession") as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"<rss></rss>")

        mock_session_instance = MagicMock()
        mock_session_instance.__aenter__ = AsyncMock(
            return_value=mock_session_instance
        )
        mock_session_instance.__aexit__ = AsyncMock()
        mock_session_instance.get = MagicMock()
        mock_session_instance.get.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_session_instance.get.return_value.__aexit__ = AsyncMock()

        mock_session.return_value = mock_session_instance

        with patch("feedparser.parse", return_value=bozo_feed):
            result = await validate_rss_feed("https://example.com/feed.xml")

    # Should still be valid if entries are present and valid
    assert result["valid"] is True
    assert result["title"] == "Test RSS Feed"


@pytest.mark.asyncio
async def test_validate_rss_feed_bozo_no_entries(mock_bozo_feed):
    """Test validation with seriously malformed feed (bozo and no entries)."""
    with patch("aiohttp.ClientSession") as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"<rss></rss>")

        mock_session_instance = MagicMock()
        mock_session_instance.__aenter__ = AsyncMock(
            return_value=mock_session_instance
        )
        mock_session_instance.__aexit__ = AsyncMock()
        mock_session_instance.get = MagicMock()
        mock_session_instance.get.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_session_instance.get.return_value.__aexit__ = AsyncMock()

        mock_session.return_value = mock_session_instance

        with patch("feedparser.parse", return_value=mock_bozo_feed):
            result = await validate_rss_feed("https://example.com/feed.xml")

    assert result["valid"] is False
    assert "Feed parsing error" in result["error"]


@pytest.mark.asyncio
async def test_validate_rss_feed_no_title(mock_valid_feed):
    """Test validation with feed that has no title."""
    feed_no_title = mock_valid_feed.copy()
    feed_no_title["feed"] = {}

    with patch("aiohttp.ClientSession") as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"<rss></rss>")

        mock_session_instance = MagicMock()
        mock_session_instance.__aenter__ = AsyncMock(
            return_value=mock_session_instance
        )
        mock_session_instance.__aexit__ = AsyncMock()
        mock_session_instance.get = MagicMock()
        mock_session_instance.get.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_session_instance.get.return_value.__aexit__ = AsyncMock()

        mock_session.return_value = mock_session_instance

        with patch("feedparser.parse", return_value=feed_no_title):
            result = await validate_rss_feed("https://example.com/feed.xml")

    # Should still be valid, just no title
    assert result["valid"] is True
    assert result["title"] is None


@pytest.mark.asyncio
async def test_validate_rss_feed_network_error():
    """Test validation with network error."""
    import aiohttp

    with patch("aiohttp.ClientSession") as mock_session:
        mock_session_instance = MagicMock()
        mock_session_instance.__aenter__ = AsyncMock(
            return_value=mock_session_instance
        )
        mock_session_instance.__aexit__ = AsyncMock()
        mock_session_instance.get = MagicMock()
        mock_session_instance.get.return_value.__aenter__ = AsyncMock(
            side_effect=aiohttp.ClientError("Connection refused")
        )

        mock_session.return_value = mock_session_instance

        result = await validate_rss_feed("https://example.com/feed.xml")

    assert result["valid"] is False
    assert "Network error" in result["error"]


@pytest.mark.asyncio
async def test_validate_rss_feed_ssrf_protection_localhost():
    """Test SSRF protection blocks localhost."""
    result = await validate_rss_feed("http://localhost/feed.xml")

    assert result["valid"] is False
    assert "localhost" in result["error"].lower()


@pytest.mark.asyncio
async def test_validate_rss_feed_ssrf_protection_private_ip():
    """Test SSRF protection blocks private IP addresses."""
    # Test private IP ranges
    private_ips = [
        "http://192.168.1.1/feed.xml",
        "http://10.0.0.1/feed.xml",
        "http://172.16.0.1/feed.xml",
        "http://127.0.0.1/feed.xml",
    ]

    for url in private_ips:
        result = await validate_rss_feed(url)
        assert result["valid"] is False
        assert (
            "private" in result["error"].lower()
            or "local" in result["error"].lower()
        ), f"Failed to block {url}"


@pytest.mark.asyncio
async def test_validate_rss_feed_ssrf_protection_loopback():
    """Test SSRF protection blocks loopback addresses."""
    result = await validate_rss_feed("http://127.0.0.1/feed.xml")

    assert result["valid"] is False
    assert (
        "private" in result["error"].lower()
        or "local" in result["error"].lower()
    )
