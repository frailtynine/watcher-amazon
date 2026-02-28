from .user import UserRead, UserCreate, UserUpdate
from .news_task import NewsTaskRead, NewsTaskCreate, NewsTaskUpdate
from .source import SourceRead, SourceCreate, SourceUpdate
from .source_news_task import SourceNewsTaskRead, SourceNewsTaskCreate
from .news_item import NewsItemRead, NewsItemCreate, NewsItemUpdate
from .news_item_news_task import (
    NewsItemNewsTaskRead,
    NewsItemNewsTaskCreate,
    NewsItemNewsTaskUpdate
)
from .newspaper import NewspaperRead

__all__ = [
    "UserRead", "UserCreate", "UserUpdate",
    "NewsTaskRead", "NewsTaskCreate", "NewsTaskUpdate",
    "SourceRead", "SourceCreate", "SourceUpdate",
    "SourceNewsTaskRead", "SourceNewsTaskCreate",
    "NewsItemRead", "NewsItemCreate", "NewsItemUpdate",
    "NewsItemNewsTaskRead", "NewsItemNewsTaskCreate", "NewsItemNewsTaskUpdate",
    "NewspaperRead",
]
