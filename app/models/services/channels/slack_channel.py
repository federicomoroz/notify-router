import httpx

from app.models.orm import EventRecord
from app.models.services.interfaces import ChannelBase


class SlackChannel(ChannelBase):
    @staticmethod
    async def send(
        http: httpx.AsyncClient,
        config: dict,
        event: EventRecord,
        payload: dict,
    ) -> tuple[bool, str]:
        webhook_url = config.get("webhook_url", "")

        if not webhook_url:
            return False, "slack config missing 'webhook_url'"

        fields = [{"type": "mrkdwn", "text": f"*{k}*: {v}"} for k, v in payload.items()]
        body = {
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"[{event.source}] {event.event_type}"},
                },
                {"type": "section", "fields": fields or [{"type": "mrkdwn", "text": "_no payload_"}]},
            ]
        }

        try:
            resp = await http.post(webhook_url, json=body)
            if resp.status_code == 200:
                return True, "Slack OK"
            return False, f"Slack {resp.status_code}: {resp.text[:200]}"
        except Exception as exc:
            return False, str(exc)
