from sqlalchemy import select

from app.db.database import get_async_session
from app.models.newspaper import Newspaper
from app.models.news_task import NewsTask
from app.models.news_item import NewsItem
from app.models.news_item_news_task import NewsItemNewsTask
from app.ai.gemini_client import GeminiClient
from app.core.config import settings

client = GeminiClient(
    api_key=settings.BACKEND_GEMINI_API_KEY,
    model_name="gemini-2.5-flash"
)


class NewsPaperProcessor:
    """Processor for news items using Gemini."""

    def __init__(self, client: GeminiClient):
        self.client = client

    async def process_newspaper(
        self,
        news_item: NewsItem,
        news_task: NewsTask,
    ) -> None:
        """Placeholder for processing newspaper items."""
        pass

    async def get_newspaper(
        self,
        news_task: NewsTask,
    ) -> Newspaper:
        """Fetch newspaper details for a given news task."""
        async for session in get_async_session():
            result = await session.execute(
                select(Newspaper).where(
                    Newspaper.news_task_id == news_task.id
                )
            )
            newspaper = result.scalar_one_or_none()
        if not newspaper:
            newspaper = await self.create_newspaper(news_task)
        return newspaper

    async def create_newspaper(
        self,
        news_task: NewsTask,
    ) -> Newspaper:
        """Create a new newspaper entry for a news task."""
        async for session in get_async_session():
            news_stmt = (
                select(NewsItem)
                .join(NewsItemNewsTask)
                .where(
                    NewsItemNewsTask.news_task_id == news_task.id,
                    NewsItemNewsTask.result.is_(True),
                    NewsItemNewsTask.processed.is_(True),
                ).order_by(NewsItem.updated_at.desc()).limit(10)
            )
            latest_processed_news = await session.execute(news_stmt)
            latest_processed_news = latest_processed_news.scalars().all()
            items_per_row = 5
            # For testing. Later created with AI
            newspaper_content = {
                f"row_{i // items_per_row + 1}": [
                    {
                        "title": news_item.title,
                        "content": news_item.content,
                        "url": news_item.url,
                        "source_id": news_item.source_id,
                        "published_at": news_item.published_at.isoformat()
                    }
                    for news_item in latest_processed_news[i:i + items_per_row]
                ]
                for i in range(0, len(latest_processed_news), items_per_row)
            }
            newspaper = Newspaper(
                news_task_id=news_task.id,
                title=f"Newspaper for Task {news_task.id}",
                body=newspaper_content
            )
            session.add(newspaper)
            await session.commit()
            await session.refresh(newspaper)
            return newspaper
