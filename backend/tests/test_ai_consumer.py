"""Tests for AI consumer."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.ai.consumer import AIConsumer
from app.ai.base import ProcessingResult
from app.models.news_item import NewsItem
from app.models.news_task import NewsTask
from app.models.news_item_news_task import NewsItemNewsTask
from app.models.source import Source, SourceType
from app.models.source_news_task import SourceNewsTask
from app.models.user import User


@pytest.fixture
def ai_consumer():
    """Create AI consumer instance."""
    return AIConsumer()


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.settings = {}
    return user


@pytest.fixture
def mock_user_no_key():
    """Create a mock user (kept for backward compat with existing tests)."""
    user = MagicMock(spec=User)
    user.id = 2
    user.email = "other@example.com"
    user.settings = {}
    return user


@pytest.fixture
async def test_news_item(db_session_maker, test_source):
    """Create a test news item."""
    async with db_session_maker() as session:
        news_item = NewsItem(
            source_id=test_source.id,
            title="Test News",
            content="This is test news content",
            url="https://example.com/news/1",
            published_at=datetime.utcnow(),
        )
        session.add(news_item)
        await session.commit()
        await session.refresh(news_item)
        return news_item


@pytest.mark.anyio
async def test_get_active_tasks(
    ai_consumer,
    db_session_maker,
    test_user,
    test_news_task
):
    """Test fetching active tasks for a user."""
    async with db_session_maker() as session:
        tasks = await ai_consumer._get_active_tasks(session, test_user.id)
        assert len(tasks) == 1
        assert tasks[0].id == test_news_task.id
        assert tasks[0].active is True


@pytest.mark.anyio
async def test_get_active_tasks_excludes_inactive(
    ai_consumer,
    db_session_maker,
    test_user
):
    """Test that inactive tasks are excluded."""
    async with db_session_maker() as session:
        # Create active task
        active_task = NewsTask(
            user_id=test_user.id,
            name="Active Task",
            prompt="Find tech news",
            active=True,
        )
        # Create inactive task
        inactive_task = NewsTask(
            user_id=test_user.id,
            name="Inactive Task",
            prompt="Find sports news",
            active=False,
        )
        session.add(active_task)
        session.add(inactive_task)
        await session.commit()

    async with db_session_maker() as session:
        consumer = AIConsumer()
        tasks = await consumer._get_active_tasks(session, test_user.id)
        assert len(tasks) == 1
        assert tasks[0].name == "Active Task"


@pytest.mark.anyio
async def test_get_unprocessed_news(
    ai_consumer,
    db_session_maker,
    test_user,
    test_news_task,
    test_source
):
    """Test fetching unprocessed news items."""
    async with db_session_maker() as session:
        # Link source to task
        source_task_link = SourceNewsTask(
            source_id=test_source.id,
            news_task_id=test_news_task.id
        )
        session.add(source_task_link)

        # Create recent news item
        recent_item = NewsItem(
            source_id=test_source.id,
            title="Recent News",
            content="Recent content",
            published_at=datetime.now() - timedelta(hours=2),
        )
        session.add(recent_item)

        # Create old news item (> 4 hours)
        old_item = NewsItem(
            source_id=test_source.id,
            title="Old News",
            content="Old content",
            published_at=datetime.now() - timedelta(hours=5),
        )
        session.add(old_item)

        await session.commit()

        # Merge the task into this session
        task_in_session = await session.merge(test_news_task)

        # Fetch unprocessed news
        consumer = AIConsumer()
        news_items = await consumer._get_unprocessed_news(
            session,
            task_in_session
        )

        # Should only get recent item
        assert len(news_items) == 1
        assert news_items[0].title == "Recent News"


@pytest.mark.anyio
async def test_save_result_creates_new_record(
    ai_consumer,
    db_session_maker,
    test_user
):
    """Test saving result creates new record."""
    # Create test data
    async with db_session_maker() as session:
        source = Source(
            user_id=test_user.id,
            name="Test Source",
            source="https://test.com/feed",
            type=SourceType.RSS
        )
        session.add(source)
        await session.commit()
        await session.refresh(source)

        news_item = NewsItem(
            source_id=source.id,
            title="Test News",
            content="Test content",
            published_at=datetime.now()
        )
        session.add(news_item)

        news_task = NewsTask(
            user_id=test_user.id,
            name="Test Task",
            prompt="Test prompt",
            active=True
        )
        session.add(news_task)
        await session.commit()
        await session.refresh(news_item)
        await session.refresh(news_task)

        result = ProcessingResult(
            result=True,
            thinking="Matches criteria",
            tokens_used=150
        )

        consumer = AIConsumer()
        await consumer._save_result(
            session,
            news_item,
            news_task,
            result
        )
        # Commit happens at higher level now
        await session.commit()

    # Verify record was created
    async with db_session_maker() as session:
        from sqlalchemy import select
        stmt = select(NewsItemNewsTask).where(
            NewsItemNewsTask.news_item_id == news_item.id,
            NewsItemNewsTask.news_task_id == news_task.id
        )
        db_result = await session.execute(stmt)
        record = db_result.scalar_one()

        assert record.processed is True
        assert record.result is True
        assert record.ai_response["thinking"] == "Matches criteria"
        assert record.ai_response["tokens_used"] == 150


@pytest.mark.anyio
async def test_save_result_updates_existing_record(
    ai_consumer,
    db_session_maker,
    test_user
):
    """Test saving result updates existing record."""
    # Create test data
    async with db_session_maker() as session:
        source = Source(
            user_id=test_user.id,
            name="Test Source",
            source="https://test.com/feed",
            type=SourceType.RSS
        )
        session.add(source)
        await session.commit()
        await session.refresh(source)

        news_item = NewsItem(
            source_id=source.id,
            title="Test News",
            content="Test content",
            published_at=datetime.now()
        )
        session.add(news_item)

        news_task = NewsTask(
            user_id=test_user.id,
            name="Test Task",
            prompt="Test prompt",
            active=True
        )
        session.add(news_task)
        await session.commit()
        await session.refresh(news_item)
        await session.refresh(news_task)

        # Create initial record
        initial_record = NewsItemNewsTask(
            news_item_id=news_item.id,
            news_task_id=news_task.id,
            processed=False,
            result=None
        )
        session.add(initial_record)
        await session.commit()

    # Update with processing result
    result = ProcessingResult(
        result=False,
        thinking="Does not match",
        tokens_used=100
    )

    async with db_session_maker() as session:
        consumer = AIConsumer()
        item_in_session = await session.merge(news_item)
        task_in_session = await session.merge(news_task)
        await consumer._save_result(
            session,
            item_in_session,
            task_in_session,
            result
        )
        # Commit happens at higher level now
        await session.commit()

    # Verify record was updated
    async with db_session_maker() as session:
        from sqlalchemy import select
        stmt = select(NewsItemNewsTask).where(
            NewsItemNewsTask.news_item_id == news_item.id,
            NewsItemNewsTask.news_task_id == news_task.id
        )
        db_result = await session.execute(stmt)
        record = db_result.scalar_one()

        assert record.processed is True
        assert record.result is False
        assert record.ai_response["thinking"] == "Does not match"


@pytest.mark.anyio
async def test_process_task_news_with_error(
    ai_consumer,
    db_session_maker,
    test_news_task,
    test_source
):
    """Test error handling during processing."""
    # Setup: Link source to task and create news item
    async with db_session_maker() as session:
        source_task_link = SourceNewsTask(
            source_id=test_source.id,
            news_task_id=test_news_task.id
        )
        session.add(source_task_link)

        news_item = NewsItem(
            source_id=test_source.id,
            title="Test News",
            content="Test content",
            published_at=datetime.utcnow() - timedelta(hours=1),
        )
        session.add(news_item)
        await session.commit()

    # Mock Nova client that raises error
    mock_client = MagicMock()
    mock_client.process_news = AsyncMock(
        side_effect=Exception("API Error")
    )

    async with db_session_maker() as session:
        consumer = AIConsumer()
        task_in_session = await session.merge(test_news_task)
        stats = await consumer._process_task_news(
            session,
            mock_client,
            task_in_session
        )

        assert stats["processed"] == 0
        assert stats["errors"] == 1


@pytest.mark.anyio
async def test_process_task_news_success(
    ai_consumer,
    db_session_maker,
    test_news_task,
    test_source
):
    """Test successful processing of news items."""
    # Setup: Link source to task and create news item
    async with db_session_maker() as session:
        source_task_link = SourceNewsTask(
            source_id=test_source.id,
            news_task_id=test_news_task.id
        )
        session.add(source_task_link)

        news_item = NewsItem(
            source_id=test_source.id,
            title="Test News",
            content="Test content",
            published_at=datetime.utcnow() - timedelta(hours=1),
        )
        session.add(news_item)
        await session.commit()

    # Mock Nova client
    mock_client = MagicMock()
    mock_client.process_news = AsyncMock(
        return_value=ProcessingResult(
            result=True,
            thinking="Test thinking",
            tokens_used=200
        )
    )

    async with db_session_maker() as session:
        consumer = AIConsumer()
        task_in_session = await session.merge(test_news_task)
        stats = await consumer._process_task_news(
            session,
            mock_client,
            task_in_session
        )

        assert stats["processed"] == 1
        assert stats["errors"] == 0
