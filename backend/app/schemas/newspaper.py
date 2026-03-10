from datetime import datetime
from typing import Any, Dict
from pydantic import BaseModel, ConfigDict, field_validator


class NewsItemPositionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    row_index: int
    position: tuple[int, int]


class NewsItemNewspaperAIResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    new_item_title: str
    new_item_summary: str
    new_item_position: tuple[int, int]
    updates: list[NewsItemPositionUpdate]


class NewsItemNewspaper(BaseModel):
    """Schema for news item representation in the newspaper."""
    title: str
    summary: str
    news_item_id: int | None
    position: tuple[int, int]
    body: str | None = None
    pub_date: datetime | None = None
    link: str | None = None
    source_name: str | None = None

    @field_validator("summary")
    @classmethod
    def summary_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("summary must not be empty")
        return v

    class Config:
        from_attributes = True


class NewspaperBody(BaseModel):
    """Schema for the newspaper body, containing multiple rows."""
    rows: list[NewsItemNewspaper]


class NewspaperBase(BaseModel):
    """Base schema for a newspaper."""
    news_task_id: int
    title: str
    body: Dict[str, Any] | NewspaperBody


class NewspaperRead(NewspaperBase):
    """Schema for reading a newspaper."""
    id: int
    updated_at: datetime
