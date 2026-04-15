import httpx

from app.models.orm import EventRecord
from app.models.services.interfaces import ChannelBase


class WebhookChannel(ChannelBase):
    @staticmethod
    async def send(
        http: httpx.AsyncClient,
        config: dict,
        event: EventRecord,
        payload: dict,
    ) -> tuple[bool, str]:
        url     = config.get("url", "")
        method  = config.get("method", "POST").upper()
        headers = config.get("headers", {})

        if not url:
            return False, "webhook config missing 'url'"

        body = {
            "source":     event.source,
            "event_type": event.event_type,
            "event_id":   event.id,
            "payload":    payload,
        }

        try:
            resp = await http.request(method, url, json=body, headers=headers)
            if 200 <= resp.status_code < 300:
                return True, f"HTTP {resp.status_code}"
            return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
        except Exception as exc:
            return False, str(exc)
