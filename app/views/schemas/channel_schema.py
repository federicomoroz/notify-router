import json

from pydantic import BaseModel, field_validator

VALID_TYPES = {"email", "telegram", "slack", "webhook"}


class ChannelIn(BaseModel):
    name:   str
    type:   str
    config: dict = {}

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v not in VALID_TYPES:
            raise ValueError(f"type must be one of {VALID_TYPES}")
        return v


class ChannelUpdate(BaseModel):
    name:   str | None = None
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
            return json.loads(v)
        return v
