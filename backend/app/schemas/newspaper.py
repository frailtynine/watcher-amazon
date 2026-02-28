from datetime import datetime
from typing import Any, Dict
from pydantic import BaseModel


class NewspaperRead(BaseModel):
    id: int
    news_task_id: int
    title: str
    body: Dict[str, Any]
    updated_at: datetime

    class Config:
        from_attributes = True
