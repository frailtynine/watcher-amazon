from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_async_session
from app.models.newspaper import Newspaper
from app.models.news_task import NewsTask
from app.models.user import User
from app.schemas.newspaper import NewspaperRead
from app.api.auth import current_active_user

router = APIRouter()


@router.get("/frontpage", response_model=NewspaperRead)
async def get_frontpage_newspaper(
    db: AsyncSession = Depends(get_async_session),
):
    """Get the first active newspaper for the public frontpage."""
    result = await db.execute(
        select(Newspaper)
        .join(NewsTask, Newspaper.news_task_id == NewsTask.id)
        .where(NewsTask.active.is_(True))
        .order_by(NewsTask.id.asc())
        .limit(1)
    )
    newspaper = result.scalar_one_or_none()
    if newspaper is None:
        raise HTTPException(
            status_code=404, detail="Frontpage newspaper not found"
        )
    return newspaper


@router.get("/{news_task_id}", response_model=NewspaperRead)
async def get_newspaper(
    news_task_id: int,
    db: AsyncSession = Depends(get_async_session),
):
    """Get the newspaper for a given news task. No authentication required."""
    result = await db.execute(
        select(Newspaper).where(Newspaper.news_task_id == news_task_id)
    )
    newspaper = result.scalar_one_or_none()
    if newspaper is None:
        raise HTTPException(
            status_code=404, detail="Newspaper not found"
        )
    return newspaper


@router.post("/{news_task_id}/regenerate", response_model=NewspaperRead)
async def regenerate_newspaper(
    news_task_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Delete the existing newspaper and rebuild it from processed news items."""
    from app.delivery.web import NewsPaperProcessor
    news_task = await db.get(NewsTask, news_task_id)
    if news_task is None:
        raise HTTPException(
            status_code=404, detail="News task not found"
        )

    existing = await db.execute(
        select(Newspaper).where(Newspaper.news_task_id == news_task_id)
    )
    newspaper = existing.scalar_one_or_none()
    if newspaper is not None:
        await db.delete(newspaper)
        await db.commit()

    processor = NewsPaperProcessor()
    new_newspaper = await processor.create_newspaper(news_task)
    return new_newspaper
