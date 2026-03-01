from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.utils import utcnow_naive


class Newspaper(Base):
    __tablename__ = "newspaper"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    news_task_id: Mapped[int] = mapped_column(
        ForeignKey("news_task.id"), nullable=False, unique=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[dict] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow_naive,
        onupdate=utcnow_naive,
        nullable=False
    )

    # Relationships
    news_task: Mapped["NewsTask"] = relationship(  # type: ignore # noqa: F821
        "NewsTask",
        back_populates="newspaper"
    )
