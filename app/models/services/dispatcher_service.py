import json

import httpx

from app.models.orm import Channel, EventRecord
from app.models.services.interfaces import ChannelBase
from app.models.services.channels.email_channel    import EmailChannel
from app.models.services.channels.telegram_channel import TelegramChannel
from app.models.services.channels.slack_channel    import SlackChannel
from app.models.services.channels.webhook_channel  import WebhookChannel


class DispatcherService:
    _registry: dict[str, type[ChannelBase]] = {
        "email":    EmailChannel,
        "telegram": TelegramChannel,
        "slack":    SlackChannel,
        "webhook":  WebhookChannel,
    }

    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self._http = http_client

    async def send(
        self,
        channel: Channel,
        event: EventRecord,
        payload: dict,
    ) -> tuple[bool, str]:
        impl = self._registry.get(channel.type)
        if not impl:
            return False, f"Unknown channel type: {channel.type}"
        try:
            config = json.loads(channel.config or "{}")
        except json.JSONDecodeError as exc:
            return False, f"Invalid channel config JSON: {exc}"
        return await impl.send(self._http, config, event, payload)
