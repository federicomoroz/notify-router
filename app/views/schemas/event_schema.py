import json
from datetime import datetime

from pydantic import BaseModel, field_validator


class EventIn(BaseModel):
    source:     str
    event_type: str
    payload:    dict = {}


class EventOut(BaseModel):
    id:          int
    source:      str
    event_type:  str
    payload:     dict
    received_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("payload", mode="before")
    @classmethod
    def parse_payload(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v
