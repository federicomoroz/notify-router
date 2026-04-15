from datetime import datetime

from pydantic import BaseModel


class LogOut(BaseModel):
    id:            int
    event_id:      int
    rule_id:       int
    channel_id:    int
    channel_type:  str
    status:        str
    response_info: str | None
    dispatched_at: datetime

    model_config = {"from_attributes": True}
