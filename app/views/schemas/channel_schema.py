import json

from pydantic import BaseModel, Field, field_validator

VALID_TYPES = {"email", "telegram", "slack", "webhook"}


class ChannelIn(BaseModel):
    name:   str = Field(min_length=1, max_length=100)
    type:   str
    config: dict = {}

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v not in VALID_TYPES:
            raise ValueError(f"type must be one of {VALID_TYPES}")
        return v


class ChannelUpdate(BaseModel):
    name:   str | None = Field(default=None, min_length=1, max_length=100)
    type:   str | None = None
    config: dict | None = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v is not None and v not in VALID_TYPES:
            raise ValueError(f"type must be one of {VALID_TYPES}")
        return v


class ChannelOut(BaseModel):
    id:     int
    name:   str
    type:   str
    config: dict

    model_config = {"from_attributes": True}

    @field_validator("config", mode="before")
    @classmethod
    def parse_config(cls, v):
        if isinstance(v, str):
            try:
                result = json.loads(v)
                return result if isinstance(result, dict) else {}
            except json.JSONDecodeError:
                return {}
        return v if isinstance(v, dict) else {}
