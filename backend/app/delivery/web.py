import logging
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import ValidationError

from app.db.database import get_async_session

from app.models.newspaper import Newspaper
from app.models.news_task import NewsTask
from app.models.news_item import NewsItem
from app.schemas.newspaper import (
    NewspaperBody,
    NewsItemNewspaperAIResponse,
    NewsItemNewspaper
)
from app.models.news_item_news_task import NewsItemNewsTask
from app.ai.nova_client import NovaClient
from app.core.config import settings

logger = logging.getLogger(__name__)

_AI_TITLE_MAX = 200
_AI_SUMMARY_MAX = 500


class NewsPaperProcessor:
    """Processor for news items using Amazon Nova."""

    async def process_newspaper(
        self,
        news_item: NewsItem,
        news_task: NewsTask,
    ) -> None:
        """Placeholder for processing newspaper items."""
        newspaper = await self.get_newspaper(news_task)
        prompt = self._get_promt(newspaper.body, news_item)
        client = NovaClient(
            aws_access_key_id=settings.BACKEND_AWS_ACCESS_KEY,
            aws_secret_access_key=settings.BACKEND_AWS_SECRET_KEY,
            region_name=settings.BACKEND_AWS_REGION,
        )
        response = await client.process_newspaper(prompt)
        new_body = self._recreate_newspaper_body(
            newspaper,
            response,
            news_item
        )
        await self._update_newspaper_body(newspaper, new_body)

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
        try:
            NewspaperBody(**newspaper.body)
        except Exception:
            logger.warning(
                "Newspaper %d has unrecognised body format, rebuilding.",
                newspaper.id,
            )
            new_body = await self._build_body_from_items(news_task)
            newspaper = await self._update_newspaper_body(newspaper, new_body)
        return newspaper

    async def create_newspaper(
        self,
        news_task: NewsTask,
    ) -> Newspaper:
        """Create a new newspaper entry for a news task."""
        body = await self._build_body_from_items(news_task)
        async for session in get_async_session():
            newspaper = Newspaper(
                news_task_id=news_task.id,
                title=f"Newspaper for Task {news_task.name}",
                body=body.model_dump(mode='json'),
            )
            session.add(newspaper)
            await session.commit()
            await session.refresh(newspaper)
            return newspaper

    async def _update_newspaper_body(
        self,
        newspaper: Newspaper,
        new_body: NewspaperBody,
    ) -> Newspaper:
        """Update the newspaper body in the database."""
        async for session in get_async_session():
            current_newspaper = await session.get(Newspaper, newspaper.id)
            if not current_newspaper:
                logger.error(
                    f"Newspaper with id {newspaper.id} not found for update."
                )
                raise ValueError(
                    f"Newspaper with id {newspaper.id} not found."
                )
            current_newspaper.body = new_body.model_dump(mode='json')
            session.add(current_newspaper)
            await session.commit()
            await session.refresh(current_newspaper)
        return current_newspaper

    async def _build_body_from_items(
        self,
        news_task: NewsTask,
    ) -> NewspaperBody:
        """Fetch processed items and build a NewspaperBody by processing each with AI."""
        from types import SimpleNamespace
        async for session in get_async_session():
            news_stmt = (
                select(NewsItem)
                .join(NewsItemNewsTask)
                .where(
                    NewsItemNewsTask.news_task_id == news_task.id,
                    NewsItemNewsTask.result.is_(True),
                    NewsItemNewsTask.processed.is_(True),
                )
                .options(selectinload(NewsItem.source))
                .order_by(NewsItem.updated_at.desc()).limit(10)
            )
            result = await session.execute(news_stmt)
            items = result.scalars().all()
        client = NovaClient(
            aws_access_key_id=settings.BACKEND_AWS_ACCESS_KEY,
            aws_secret_access_key=settings.BACKEND_AWS_SECRET_KEY,
            region_name=settings.BACKEND_AWS_REGION,
        )
        current_body = NewspaperBody(rows=[])
        for item in items:
            mock = SimpleNamespace(body=current_body.model_dump())
            prompt = self._get_promt(mock.body, item)
            response = await client.process_newspaper(prompt)
            try:
                current_body = self._recreate_newspaper_body(
                    mock, response, item
                )
            except Exception as e:
                logger.error(
                    "Skipping item %s while building newspaper body: %s",
                    item.id, e,
                )
                continue
        return current_body

    def _get_promt(
        self,
        newspaper_body: dict,
        news_item: NewsItem,
    ) -> str:
        newspaper_schema = NewspaperBody(**newspaper_body)
        newspaper_schema = newspaper_schema.model_dump_json()
        return (
            "You are the publishing editor of a news website in English.\n\n"
            "Your task:\n"
            "1. Write a concise, engaging headline (NYT style, not tabloid) "
            f"for the news item below. Max {_AI_TITLE_MAX} characters.\n"
            "2. Write a summary of no more than 3 sentences. "
            f"Max {_AI_SUMMARY_MAX} characters.\n"
            "3. Rearrange the news items in the newspaper body"
            "according to their importance, finding the best place for the new "
            "item. Keep no more than 10 rows."
            "The goal is to create a relevant news picture of the last few hours"
            " or the day, depending on the news flow. "
            "Feel free to delete old items to make space for new ones or "
            "rearrange the whole layout if needed. \n"
            "Layout rules:\n"
            "- Row with 1 item = headline story (most important and urgent).\n"
            "- Row with 2 items = important but less recent.\n"
            "- Row with 3 to 5 items = everything else.\n"
            "- Never add to a row that already has 5 items.\n\n"
            "Keep the layout diverse, don't put two rows of two items next to each other. \n"
            "No news items should be ever duplicated or repeated.\n"
            "If the new news item is almost the same as an existing one, "
            "keep the one that is more recent and relevant, and drop the other.\n\n"
            "Output instructions:\n"
            "Return a raw JSON object with exactly these fields "
            "(no markdown, no code fences):\n"
            "- `new_item_title`: headline for the new item (string)\n"
            "- `new_item_summary`: 1-3 sentence summary (string)\n"
            "- `new_item_position`: [row, col] where to place the new item (array of 2 ints)\n"
            "- `updates`: array of objects, each with exactly TWO fields:\n"
            "    - `row_index` (int): 0-based index of the item in the `rows` array of the current layout\n"
            "    - `position` (array of 2 ints): new [row, col] position for that item\n"
            "  Include only items you want to KEEP. Omit items you want to drop.\n"
            "  Do NOT include title, summary, news_item_id, or any other fields in updates.\n\n"
            "Example output format:\n"
            '{"new_item_title":"...", "new_item_summary":"...", "new_item_position":[0,0], '
            '"updates":[{"row_index":0,"position":[1,0]},{"row_index":2,"position":[2,0]}]}\n\n'
            f"Current layout (rows is a 0-based array): {newspaper_schema}\n\n"
            "News item to place:\n"
            f"Title: {news_item.title}\n"
            f"Content: {news_item.content}"
        )

    def _recreate_newspaper_body(
        self,
        newspaper: Newspaper,
        response: str,
        news_item: NewsItem,
    ) -> NewspaperBody:
        logger.debug("Raw AI response: %s", response)
        try:
            ai_response = NewsItemNewspaperAIResponse.model_validate_json(
                response
            )
        except ValidationError as e:
            logger.error(
                f"Failed to parse AI response: {e}\nRaw response: {response}"
            )
            raise
        current_body = NewspaperBody(**newspaper.body)
        current_body_items = current_body.rows
        new_item = NewsItemNewspaper(
            title=ai_response.new_item_title,
            summary=ai_response.new_item_summary,
            position=ai_response.new_item_position,
            news_item_id=news_item.id,
            pub_date=news_item.published_at,
            link=news_item.url,
            source_name=news_item.source.name if news_item.source else None,
        )
        new_body = [new_item]
        for update in ai_response.updates:
            if update.row_index >= len(current_body_items):
                logger.warning(
                    f"AI returned out-of-bounds index "
                    f"{update.row_index} (body has "
                    f"{len(current_body_items)} items), skipping."
                )
                continue
            item_to_push = current_body_items[update.row_index]
            item_to_push.position = update.position
            new_body.append(item_to_push)
        return NewspaperBody(rows=new_body)
