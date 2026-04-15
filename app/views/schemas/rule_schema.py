from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class RuleIn(BaseModel):
    name:              str = Field(min_length=1, max_length=100)
    source_filter:     str = Field(default="*", max_length=100)
    event_type_filter: str = Field(default="*", max_length=100)
    condition_key:     str | None = Field(default=None, max_length=100)
    condition_value:   str | None = Field(default=None, max_length=255)
    channel_id:        int
    enabled:           bool = True
    priority:          int = 0

    @model_validator(mode="after")
    def check_condition_pair(self):
        if (self.condition_key is None) != (self.condition_value is None):
            raise ValueError("condition_key and condition_value must both be set or both be null")
        return self


class RuleUpdate(BaseModel):
    name:              str | None = Field(default=None, min_length=1, max_length=100)
    source_filter:     str | None = Field(default=None, max_length=100)
    event_type_filter: str | None = Field(default=None, max_length=100)
    condition_key:     str | None = Field(default=None, max_length=100)
    condition_value:   str | None = Field(default=None, max_length=255)
    channel_id:        int | None = None
    enabled:           bool | None = None
    priority:          int | None = None

    @model_validator(mode="after")
    def check_condition_pair(self):
        # Only validate consistency when BOTH fields are explicitly sent in the same request.
        # Using model_fields_set to distinguish "not sent" (default None) from "explicitly sent".
        explicitly_set = self.model_fields_set
        key_sent = "condition_key" in explicitly_set
        val_sent = "condition_value" in explicitly_set

        if key_sent and val_sent:
            # Both provided: they must both be set or both be null
            if (self.condition_key is None) != (self.condition_value is None):
                raise ValueError("condition_key and condition_value must both be set or both be null")
        elif key_sent and self.condition_key is not None and not val_sent:
            raise ValueError("condition_value is required when setting condition_key")
        elif val_sent and self.condition_value is not None and not key_sent:
            raise ValueError("condition_key is required when setting condition_value")
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
