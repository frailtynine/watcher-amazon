"""AI consumer for processing news items."""

import logging
from datetime import timedelta
import asyncio

from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.nova_client import NovaClient
from app.ai.base import ProcessingResult
from app.models.news_item import NewsItem
from app.models.news_task import NewsTask
from app.models.news_item_news_task import NewsItemNewsTask
from app.models.source_news_task import SourceNewsTask
from app.delivery.web import NewsPaperProcessor
from app.models.user import User
from app.models.utils import utcnow_naive
from app.core.config import settings
from app.db.database import get_async_session

logger = logging.getLogger(__name__)


class AIConsumer:
    """Consumer for processing news items with AI."""

    def __init__(self):
        """Initialize AI consumer."""
        self.logger = logger.getChild(self.__class__.__name__)

    async def process_user_news(
        self,
        user_id: int
    ) -> dict:
        """Process all unprocessed news for a user's active tasks.

        Args:
            user_id: User ID

        Returns:
            Dict with processing statistics
        """
        async for db in get_async_session():
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            user: User = result.scalar_one_or_none()

            if not user:
                self.logger.warning(f"User with ID {user_id} not found")
                return {"processed": 0, "errors": 0}
            client = self._create_ai_client()
            tasks = await self._get_active_tasks(db, user.id)

            total_processed = 0
            total_errors = 0

            for task in tasks:
                stats = await self._process_task_news(db, client, task)
                total_processed += stats["processed"]
                total_errors += stats["errors"]
            await db.commit()

            return {
                "processed": total_processed,
                "errors": total_errors
            }

    async def _process_task_news(
        self,
        db: AsyncSession,
        client: NovaClient,
        task: NewsTask,
    ) -> dict:
        """Process unprocessed news items for a specific task.

        Args:
            db: Database session
            client: Amazon Nova client
            task: NewsTask instance

        Returns:
            Dict with processing statistics: {"processed": int, "errors": int}
        """
        news_items = await self._get_unprocessed_news(db, task)

        if not news_items:
            return {"processed": 0, "errors": 0}

        tasks = []
        for news_item in news_items:
            tasks.append(
                self._process_task_news_concurrent(client, news_item, task, db)
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        try:
            await db.commit()
        except Exception as e:
            self.logger.error(
                f"Error committing results for task {task.id}: {e}",
                exc_info=True
                )
            await db.rollback()
            # Count all as errors if commit fails
            return {"processed": 0, "errors": len(news_items)}

        # Count successes and errors
        processed = sum(
            1 for r in results if r and not isinstance(r, Exception)
        )
        errors = sum(
            1 for r in results if isinstance(r, Exception) or r is None
        )

        # if processed > 0:
        try:
            processor = NewsPaperProcessor()
            for news_item in news_items:
                await processor.process_newspaper(
                    news_task=task,
                    news_item=news_item
                )
        except Exception as e:
            self.logger.error(
                f"Error generating newspaper for task {task.id}: {e}",
                exc_info=True
            )

        return {"processed": processed, "errors": errors}

    async def _process_task_news_concurrent(
        self,
        client: NovaClient,
        news_item: NewsItem,
        task: NewsTask,
        db: AsyncSession
    ) -> ProcessingResult | None:
        """Process a single news item concurrently.

        Args:
            client: Amazon Nova client
            news_item: NewsItem instance
            task: NewsTask instance
        Returns:
            ProcessingResult instance or None if error occurs
        """
        try:
            result = await client.process_news(
                title=news_item.title,
                content=news_item.content,
                prompt=task.prompt
            )

            await self._save_result(db, news_item, task, result)
            self.logger.debug(
                f"Processed news {news_item.id} with task {task.id}: "
                f"result={result.result}"
            )
            return result
        except Exception as e:
            self.logger.error(
                f"Error processing news {news_item.id} concurrently: {e}",
                exc_info=True
            )
            return None

    async def _get_active_tasks(
        self,
        db: AsyncSession,
        user_id: int
    ) -> list[NewsTask]:
        """Get all active tasks for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of active NewsTask instances
        """
        stmt = select(NewsTask).where(
            and_(
                NewsTask.user_id == user_id,
                NewsTask.active.is_(True)
            )
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def _get_unprocessed_news(
        self,
        db: AsyncSession,
        task: NewsTask
    ) -> list[NewsItem]:
        """Get unprocessed news items for a task (< 4 hours old).

        Args:
            db: Database session
            task: NewsTask instance

        Returns:
            List of NewsItem instances
        """
        cutoff_time = utcnow_naive() - timedelta(hours=4)

        # Get sources linked to this task
        stmt = (
            select(NewsItem)
            .join(
                SourceNewsTask,
                NewsItem.source_id == SourceNewsTask.source_id
            )
            .outerjoin(
                NewsItemNewsTask,
                and_(
                    NewsItemNewsTask.news_item_id == NewsItem.id,
                    NewsItemNewsTask.news_task_id == task.id
                )
            )
            .where(
                and_(
                    SourceNewsTask.news_task_id == task.id,
                    NewsItem.published_at >= cutoff_time,
                    or_(
                        NewsItemNewsTask.news_item_id.is_(None),
                        NewsItemNewsTask.processed.is_(False)
                    )
                )
            )
            .distinct(NewsItem.id)
            .options(selectinload(NewsItem.source))
        )

        result = await db.execute(stmt)
        return result.scalars().all()

    async def _save_result(
        self,
        db: AsyncSession,
        news_item: NewsItem,
        task: NewsTask,
        result
    ) -> None:
        """Save processing result to database.

        Args:
            db: Database session
            news_item: NewsItem instance
            task: NewsTask instance
            result: ProcessingResult instance
        """
        # Check if record exists
        stmt = select(NewsItemNewsTask).where(
            and_(
                NewsItemNewsTask.news_item_id == news_item.id,
                NewsItemNewsTask.news_task_id == task.id
            )
        )
        existing = await db.execute(stmt)
        record = existing.scalar_one_or_none()

        ai_response = {
            "thinking": result.thinking,
            "tokens_used": result.tokens_used,
            "processed_at": utcnow_naive().isoformat()
        }

        if record:
            # Update existing record
            record.processed = True
            record.result = result.result
            record.processed_at = utcnow_naive()
            record.ai_response = ai_response
        else:
            # Create new record
            record = NewsItemNewsTask(
                news_item_id=news_item.id,
                news_task_id=task.id,
                processed=True,
                result=result.result,
                processed_at=utcnow_naive(),
                ai_response=ai_response
            )
            db.add(record)

    def _create_ai_client(self) -> NovaClient:
        """Create an Amazon Nova AI client using global AWS credentials.

        Returns:
            Configured NovaClient instance
        """
        return NovaClient(
            aws_access_key_id=settings.BACKEND_AWS_ACCESS_KEY,
            aws_secret_access_key=settings.BACKEND_AWS_SECRET_KEY,
            region_name=settings.BACKEND_AWS_REGION,
        )


async def run_ai_consumer_job():
    """Run AI consumer job for all active users."""
    consumer = AIConsumer()
    async for users_db_session in get_async_session():
        # Get all active users
        stmt = select(User.id).where(User.is_active.is_(True))
        result = await users_db_session.execute(stmt)
        user_ids = result.scalars().all()

    user_tasks = []
    for user_id in user_ids:
        user_tasks.append(consumer.process_user_news(user_id))
    results = await asyncio.gather(*user_tasks)
    logger.info(results)
