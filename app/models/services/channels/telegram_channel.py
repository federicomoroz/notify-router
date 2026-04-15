import httpx

from app.models.orm import EventRecord
from app.models.services.interfaces import ChannelBase


class TelegramChannel(ChannelBase):
    @staticmethod
    async def send(
        http: httpx.AsyncClient,
        config: dict,
        event: EventRecord,
        payload: dict,
    ) -> tuple[bool, str]:
        bot_token = config.get("bot_token", "")
        chat_id   = config.get("chat_id", "")

        if not bot_token or not chat_id:
            return False, "telegram config missing 'bot_token' or 'chat_id'"

        text = (
            f"*[{event.source}]* `{event.event_type}`\n"
            + "\n".join(f"• *{k}*: {v}" for k, v in payload.items())
        )
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        try:
            resp = await http.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
            if resp.status_code == 200:
                return True, f"Telegram OK (msg_id={resp.json().get('result', {}).get('message_id')})"
            return False, f"Telegram {resp.status_code}: {resp.text[:200]}"
        except Exception as exc:
            return False, str(exc)
