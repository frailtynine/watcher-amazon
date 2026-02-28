from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_async_session
from app.models.newspaper import Newspaper
from app.schemas.newspaper import NewspaperRead

router = APIRouter()


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
        raise HTTPException(status_code=404, detail="Newspaper not found")
    return newspaper
