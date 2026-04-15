import json
from datetime import datetime

from pydantic import BaseModel, field_validator, model_validator


class EventIn(BaseModel):
    source:     str
    event_type: str
    payload:    dict = {}

    @model_validator(mode="after")
    def check_payload_size(self):
        if len(json.dumps(self.payload)) > 4000:
            raise ValueError("payload must not exceed 4000 characters when serialized")
        return self


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
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v
