import pytest
from httpx import AsyncClient
from unittest.mock import patch
from app.models import Source

pytestmark = pytest.mark.anyio


async def test_create_source_success(client: AsyncClient, auth_headers: dict):
    """Test creating a source with valid data."""
    # Mock RSS validation
    with patch("app.api.sources.validate_rss_feed") as mock_validate:
        mock_validate.return_value = {
            "valid": True,
            "url": "https://example.com/feed.xml",
            "title": "Test Feed Title",
            "error": None
        }

        response = await client.post(
            "/api/sources/",
            headers=auth_headers,
            json={
                "name": "My RSS Feed",
                "type": "RSS",
                "source": "https://example.com/feed.xml",
                "active": True,
            },
        )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Feed Title"
    assert data["type"] == "RSS"
    assert "id" in data


async def test_create_source_missing_name(
    client: AsyncClient,
    auth_headers: dict
):
    """Test creating source fails without name."""
    response = await client.post(
        "/api/sources/",
        headers=auth_headers,
        json={
            "type": "RSS",
            "source": "https://example.com/feed.xml",
        },
    )
    assert response.status_code == 422


async def test_create_source_empty_name(
    client: AsyncClient,
    auth_headers: dict
):
    """Test creating source fails with empty name."""
    response = await client.post(
        "/api/sources/",
        headers=auth_headers,
        json={
            "name": "",
            "type": "RSS",
            "source": "https://example.com/feed.xml",
        },
    )
    assert response.status_code == 422


async def test_create_source_invalid_type(
    client: AsyncClient,
    auth_headers: dict
):
    """Test creating source fails with invalid type."""
    response = await client.post(
        "/api/sources/",
        headers=auth_headers,
        json={
            "name": "Test Source",
            "type": "invalid_type",
            "source": "https://example.com",
        },
    )
    assert response.status_code == 422


async def test_create_source_unauthorized(client: AsyncClient):
    """Test creating source requires authentication."""
    response = await client.post(
        "/api/sources/",
        json={
            "name": "Test Source",
            "type": "RSS",
            "source": "https://example.com/feed.xml",
        },
    )
    assert response.status_code == 401


async def test_list_sources_empty(client: AsyncClient, auth_headers: dict):
    """Test listing sources when empty."""
    response = await client.get("/api/sources/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


async def test_list_sources(
    client: AsyncClient,
    auth_headers: dict,
    test_source: Source,
):
    """Test listing sources."""
    response = await client.get("/api/sources/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Source"


async def test_list_sources_unauthorized(client: AsyncClient):
    """Test listing sources requires authentication."""
    response = await client.get("/api/sources/")
    assert response.status_code == 401


async def test_get_source(
    client: AsyncClient,
    auth_headers: dict,
    test_source: Source,
):
    """Test getting a specific source."""
    response = await client.get(
        f"/api/sources/{test_source.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_source.id
    assert data["name"] == "Test Source"


async def test_get_source_not_found(client: AsyncClient, auth_headers: dict):
    """Test getting non-existent source returns 404."""
    response = await client.get("/api/sources/99999", headers=auth_headers)
    assert response.status_code == 404


async def test_get_source_unauthorized(
    client: AsyncClient,
    test_source: Source,
):
    """Test getting source requires authentication."""
    response = await client.get(f"/api/sources/{test_source.id}")
    assert response.status_code == 401


async def test_update_source(
    client: AsyncClient,
    auth_headers: dict,
    test_source: Source,
):
    """Test updating a source."""
    response = await client.patch(
        f"/api/sources/{test_source.id}",
        headers=auth_headers,
        json={
            "name": "Updated Source Name",
            "active": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Source Name"
    assert data["active"] is False


async def test_update_source_invalid_name(
    client: AsyncClient,
    auth_headers: dict,
    test_source: Source,
):
    """Test updating source with empty name fails."""
    response = await client.patch(
        f"/api/sources/{test_source.id}",
        headers=auth_headers,
        json={"name": ""},
    )
    assert response.status_code == 422


async def test_update_source_not_found(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test updating non-existent source returns 404."""
    response = await client.patch(
        "/api/sources/99999",
        headers=auth_headers,
        json={"name": "Updated Name"},
    )
    assert response.status_code == 404


async def test_delete_source(
    client: AsyncClient,
    auth_headers: dict,
    test_source: Source,
):
    """Test deleting a source."""
    response = await client.delete(
        f"/api/sources/{test_source.id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # Verify it's gone
    response = await client.get(
        f"/api/sources/{test_source.id}",
        headers=auth_headers,
    )
    assert response.status_code == 404


async def test_delete_source_not_found(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test deleting non-existent source returns 404."""
    response = await client.delete("/api/sources/99999", headers=auth_headers)
    assert response.status_code == 404


async def test_create_rss_source_with_invalid_feed(
    client: AsyncClient, auth_headers: dict
):
    """Test creating RSS source with invalid feed."""
    with patch("app.api.sources.validate_rss_feed") as mock_validate:
        mock_validate.return_value = {
            "valid": False,
            "url": "https://example.com/invalid.xml",
            "title": None,
            "error": "Feed has no entries"
        }

        response = await client.post(
            "/api/sources/",
            headers=auth_headers,
            json={
                "name": "Invalid Feed",
                "type": "RSS",
                "source": "https://example.com/invalid.xml",
                "active": True,
            },
        )

    assert response.status_code == 400
    assert "Invalid RSS feed" in response.json()["detail"]
    assert "Feed has no entries" in response.json()["detail"]


async def test_create_rss_source_auto_populate_name(
    client: AsyncClient, auth_headers: dict
):
    """Test creating RSS source auto-populates name from feed title."""
    with patch("app.api.sources.validate_rss_feed") as mock_validate:
        mock_validate.return_value = {
            "valid": True,
            "url": "https://example.com/feed.xml",
            "title": "Awesome Tech Blog",
            "error": None
        }

        response = await client.post(
            "/api/sources/",
            headers=auth_headers,
            json={
                "name": "My RSS Feed",  # Generic name
                "type": "RSS",
                "source": "https://example.com/feed.xml",
                "active": True,
            },
        )

    assert response.status_code == 201
    data = response.json()
    # Should use feed title instead of generic name
    assert data["name"] == "Awesome Tech Blog"
    assert data["type"] == "RSS"


async def test_create_rss_source_keep_custom_name(
    client: AsyncClient, auth_headers: dict
):
    """Test creating RSS source keeps custom name."""
    with patch("app.api.sources.validate_rss_feed") as mock_validate:
        mock_validate.return_value = {
            "valid": True,
            "url": "https://example.com/feed.xml",
            "title": "Awesome Tech Blog",
            "error": None
        }

        response = await client.post(
            "/api/sources/",
            headers=auth_headers,
            json={
                "name": "My Custom Name",  # Specific custom name
                "type": "RSS",
                "source": "https://example.com/feed.xml",
                "active": True,
            },
        )

    assert response.status_code == 201
    data = response.json()
    # Should keep custom name
    assert data["name"] == "My Custom Name"
    assert data["type"] == "RSS"


async def test_create_rss_source_malformed_url(
    client: AsyncClient, auth_headers: dict
):
    """Test creating RSS source with malformed URL."""
    with patch("app.api.sources.validate_rss_feed") as mock_validate:
        mock_validate.return_value = {
            "valid": False,
            "url": "not-a-url",
            "title": None,
            "error": "URL must start with http:// or https://"
        }

        response = await client.post(
            "/api/sources/",
            headers=auth_headers,
            json={
                "name": "Bad URL Feed",
                "type": "RSS",
                "source": "not-a-url",
                "active": True,
            },
        )

    assert response.status_code == 400
    assert "Invalid RSS feed" in response.json()["detail"]


async def test_create_rss_source_http_error(
    client: AsyncClient, auth_headers: dict
):
    """Test creating RSS source when feed returns HTTP error."""
    with patch("app.api.sources.validate_rss_feed") as mock_validate:
        mock_validate.return_value = {
            "valid": False,
            "url": "https://example.com/feed.xml",
            "title": None,
            "error": "HTTP error: status code 404"
        }

        response = await client.post(
            "/api/sources/",
            headers=auth_headers,
            json={
                "name": "Not Found Feed",
                "type": "RSS",
                "source": "https://example.com/feed.xml",
                "active": True,
            },
        )

    assert response.status_code == 400
    assert "Invalid RSS feed" in response.json()["detail"]
    assert "404" in response.json()["detail"]
