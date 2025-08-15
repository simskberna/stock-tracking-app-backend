# app/events/event_bus.py
import asyncio
from typing import Dict, List, Callable, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    CRITICAL_STOCK = "critical_stock"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    ORDER_CREATED = "order_created"


class EventBus:
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}

    def subscribe(self, event_type: EventType, handler: Callable):
        """Bir event tipine handler ekler"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    async def publish(self, event_type: EventType, data: Dict[str, Any]):
        """Event yayınlar ve tüm subscriber'lara gönderir"""
        if event_type in self._subscribers:
            tasks = []
            for handler in self._subscribers[event_type]:
                try:
                    task = asyncio.create_task(handler(data))
                    tasks.append(task)
                except Exception as e:
                    logger.error(f"Error creating task for handler {handler.__name__}: {e}")

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)


# Global event bus instance
event_bus = EventBus()
