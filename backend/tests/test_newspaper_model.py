import pytest
import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.models.news_task import NewsTask
from app.models.newspaper import Newspaper

pytestmark = pytest.mark.anyio


def make_user(**kwargs):
    defaults = dict(
        email=f"user_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=False,
        is_superuser=False,
    )
    return User(**{**defaults, **kwargs})


def make_news_task(user_id, **kwargs):
    defaults = dict(
        user_id=user_id,
        name="Test Task",
        prompt="Filter AI news",
        active=True,
    )
    return NewsTask(**{**defaults, **kwargs})


async def test_create_newspaper(db_session):
    """Newspaper can be created with title, body, and updated_at."""
    user = make_user()
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    task = make_news_task(user.id)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    newspaper = Newspaper(
        news_task_id=task.id,
        title="Weekly AI Digest",
        body={"sections": ["AI", "ML"], "items": []},
    )
    db_session.add(newspaper)
    await db_session.commit()
    await db_session.refresh(newspaper)

    assert newspaper.id is not None
    assert newspaper.news_task_id == task.id
    assert newspaper.title == "Weekly AI Digest"
    assert newspaper.body == {"sections": ["AI", "ML"], "items": []}
    assert isinstance(newspaper.updated_at, datetime)


async def test_newspaper_relationship(db_session):
    """Newspaper.news_task relationship resolves correctly."""
    user = make_user()
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    task = make_news_task(user.id)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    newspaper = Newspaper(
        news_task_id=task.id,
        title="Digest",
        body={},
    )
    db_session.add(newspaper)
    await db_session.commit()
    await db_session.refresh(newspaper)

    result = await db_session.execute(
        select(Newspaper).where(Newspaper.id == newspaper.id)
    )
    fetched = result.scalar_one()
    assert fetched.news_task_id == task.id


async def test_news_task_back_populates_newspaper(db_session):
    """NewsTask.newspaper back-populates to the Newspaper instance."""
    user = make_user()
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    task = make_news_task(user.id)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    newspaper = Newspaper(
        news_task_id=task.id,
        title="Digest",
        body={"key": "value"},
    )
    db_session.add(newspaper)
    await db_session.commit()

    result = await db_session.execute(
        select(NewsTask).where(NewsTask.id == task.id)
    )
    fetched_task = result.scalar_one()
    await db_session.refresh(fetched_task, ["newspaper"])

    assert fetched_task.newspaper is not None
    assert fetched_task.newspaper.title == "Digest"


async def test_newspaper_one_to_one_unique(db_session):
    """A NewsTask can only have one Newspaper (unique constraint)."""
    user = make_user()
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    task = make_news_task(user.id)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    db_session.add(Newspaper(news_task_id=task.id, title="First", body={}))
    await db_session.commit()

    db_session.add(Newspaper(news_task_id=task.id, title="Second", body={}))
    with pytest.raises(IntegrityError):
        await db_session.commit()

    await db_session.rollback()


async def test_newspaper_cascade_delete(db_session):
    """Deleting a NewsTask cascades to its Newspaper."""
    user = make_user()
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    task = make_news_task(user.id)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    newspaper = Newspaper(
        news_task_id=task.id,
        title="To be deleted",
        body={},
    )
    db_session.add(newspaper)
    await db_session.commit()
    newspaper_id = newspaper.id

    await db_session.delete(task)
    await db_session.commit()

    result = await db_session.execute(
        select(Newspaper).where(Newspaper.id == newspaper_id)
    )
    assert result.scalar_one_or_none() is None


async def test_newspaper_body_stores_nested_json(db_session):
    """Body field persists arbitrary nested JSON."""
    user = make_user()
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    task = make_news_task(user.id)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    body = {
        "sections": [
            {"title": "AI", "articles": [{"url": "https://example.com"}]},
        ],
        "meta": {"count": 1, "generated": True},
    }
    newspaper = Newspaper(news_task_id=task.id, title="Digest", body=body)
    db_session.add(newspaper)
    await db_session.commit()
    await db_session.refresh(newspaper)

    assert newspaper.body == body
    assert newspaper.body["sections"][0]["title"] == "AI"
    assert newspaper.body["meta"]["count"] == 1
