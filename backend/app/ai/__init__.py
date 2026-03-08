"""AI module for news processing."""

from app.ai.nova_client import NovaClient
from app.ai.consumer import AIConsumer

__all__ = ["NovaClient", "AIConsumer"]
