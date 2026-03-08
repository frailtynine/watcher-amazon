from contextlib import asynccontextmanager
import logging
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core import settings
from app.db import engine
from app.api import api_router
from app.producers.rss import rss_producer_job
from app.producers.telegram import telegram_producer_job
from app.ai.consumer import run_ai_consumer_job

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler = AsyncIOScheduler()
    scheduler.start()
    app.state.scheduler = scheduler

    # Schedule RSS producer job
    scheduler.add_job(
        rss_producer_job,
        trigger=IntervalTrigger(
            minutes=settings.RSS_FETCH_INTERVAL_MINUTES
        ),
        id="rss_producer",
        name="RSS Feed Producer",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.add_job(
        run_ai_consumer_job,
        trigger=IntervalTrigger(minutes=1),
        id="ai_consumer",
        name="AI Consumer Job",
        replace_existing=True,
        max_instances=1,
    )
    telegram_producer_task = asyncio.create_task(telegram_producer_job(
        api_id=settings.BACKEND_TG_API_ID,
        api_hash=settings.BACKEND_TG_API_HASH,
        session_string=settings.BACKEND_TG_SESSION_STRING
    ))
    app.state.telegram_producer_task = telegram_producer_task
    logger.info(
        f"Scheduled RSS producer job to run every "
        f"{settings.RSS_FETCH_INTERVAL_MINUTES} minutes"
    )

    yield

    # Cleanup on shutdown
    telegram_producer_task.cancel()
    try:
        await telegram_producer_task
    except asyncio.CancelledError:
        logger.info("Telegram producer task cancelled successfully")
    scheduler.shutdown(wait=True)
    await engine.dispose()


def get_app() -> FastAPI:
    """Application factory for creating FastAPI app instance."""
    application = FastAPI(
        title="NewsWatcher API",
        description="NewsWatcher Backend API with Authentication",
        version="0.1.0",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router, prefix="/api")

    @application.get("/")
    async def root():
        return {"message": "NewsWatcher API", "version": "0.1.0"}

    @application.get("/health")
    async def health():
        return {"status": "healthy"}

    return application


app = get_app()
