from fastapi import APIRouter
from .auth import router as auth_router
from .news_tasks import router as news_tasks_router
from .sources import router as sources_router
from .source_news_tasks import router as source_news_tasks_router
from .news_items import router as news_items_router
from .newspapers import router as newspapers_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="", tags=["auth"])
api_router.include_router(
    news_tasks_router, prefix="/news-tasks", tags=["news-tasks"]
)
api_router.include_router(sources_router, prefix="/sources", tags=["sources"])
api_router.include_router(
    source_news_tasks_router,
    prefix="/associations",
    tags=["associations"],
)
api_router.include_router(
    news_items_router, prefix="/news-items", tags=["news-items"]
)
api_router.include_router(
    newspapers_router, prefix="/newspapers", tags=["newspapers"]
)
