import httpx
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.core.config import SENDER_EMAIL, SENDGRID_API_KEY
from app.models.orm import EventRecord
from app.models.services.interfaces import ChannelBase


class EmailChannel(ChannelBase):
    @staticmethod
    async def send(
        http: httpx.AsyncClient,
        config: dict,
        event: EventRecord,
        payload: dict,
    ) -> tuple[bool, str]:
        to_addr        = config.get("to", "")
        subject_tmpl   = config.get("subject_template", "[{source}] {event_type}")
        subject        = subject_tmpl.format(source=event.source, event_type=event.event_type)

        if not to_addr:
            return False, "email config missing 'to' address"
        if not SENDGRID_API_KEY:
            return False, "SENDGRID_API_KEY not configured"

        body = (
            f"<strong>Source:</strong> {event.source}<br>"
            f"<strong>Event:</strong> {event.event_type}<br>"
            f"<strong>Payload:</strong><pre>{payload}</pre>"
        )

        try:
            message = Mail(
                from_email=SENDER_EMAIL,
                to_emails=to_addr,
                subject=subject,
                html_content=body,
            )
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg.send(message)
            return True, f"SendGrid status {response.status_code}"
        except Exception as exc:
            return False, str(exc)
