from abc import ABC, abstractmethod

import httpx

from app.models.orm import EventRecord


class ChannelBase(ABC):
    @staticmethod
    @abstractmethod
    async def send(
        http: httpx.AsyncClient,
        config: dict,
        event: EventRecord,
        payload: dict,
    ) -> tuple[bool, str]:
        """Send a notification. Returns (success, info_message)."""
        ...
