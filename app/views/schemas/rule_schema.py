from datetime import datetime

from pydantic import BaseModel, model_validator


def _validate_condition_pair(values):
    key = values.get("condition_key") if isinstance(values, dict) else getattr(values, "condition_key", None)
    val = values.get("condition_value") if isinstance(values, dict) else getattr(values, "condition_value", None)
    if (key is None) != (val is None):
        raise ValueError("condition_key and condition_value must both be set or both be null")
    return values


class RuleIn(BaseModel):
    name:              str
    source_filter:     str = "*"
    event_type_filter: str = "*"
    condition_key:     str | None = None
    condition_value:   str | None = None
    channel_id:        int
    enabled:           bool = True
    priority:          int = 0

    @model_validator(mode="after")
    def check_condition_pair(self):
        if (self.condition_key is None) != (self.condition_value is None):
            raise ValueError("condition_key and condition_value must both be set or both be null")
        return self


class RuleUpdate(BaseModel):
    name:              str | None = None
    source_filter:     str | None = None
    event_type_filter: str | None = None
    condition_key:     str | None = None
    condition_value:   str | None = None
    channel_id:        int | None = None
    enabled:           bool | None = None
    priority:          int | None = None

    @model_validator(mode="after")
    def check_condition_pair(self):
        # Only validate when both fields are explicitly provided in the update
        if self.condition_key is not None and self.condition_value is None:
            raise ValueError("condition_value is required when condition_key is set")
        if self.condition_value is not None and self.condition_key is None:
            raise ValueError("condition_key is required when condition_value is set")
        return self


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
