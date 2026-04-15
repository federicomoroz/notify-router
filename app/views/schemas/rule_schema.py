from datetime import datetime

from pydantic import BaseModel


class RuleIn(BaseModel):
    name:              str
    source_filter:     str = "*"
    event_type_filter: str = "*"
    condition_key:     str | None = None
    condition_value:   str | None = None
    channel_id:        int
    enabled:           bool = True
    priority:          int = 0


class RuleUpdate(BaseModel):
    name:              str | None = None
    source_filter:     str | None = None
    event_type_filter: str | None = None
    condition_key:     str | None = None
    condition_value:   str | None = None
    channel_id:        int | None = None
    enabled:           bool | None = None
    priority:          int | None = None


class RuleOut(BaseModel):
    id:                int
    name:              str
    source_filter:     str
    event_type_filter: str
    condition_key:     str | None
    condition_value:   str | None
    channel_id:        int
    enabled:           bool
    priority:          int
    created_at:        datetime

    model_config = {"from_attributes": True}
