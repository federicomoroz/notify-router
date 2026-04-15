from dataclasses import dataclass


@dataclass(frozen=True)
class EventReceived:
    event_id:   int
    source:     str
    event_type: str


@dataclass(frozen=True)
class DispatchSucceeded:
    event_id:     int
    rule_id:      int
    channel_id:   int
    channel_type: str


@dataclass(frozen=True)
class DispatchFailed:
    event_id:     int
    rule_id:      int
    channel_id:   int
    channel_type: str
    error:        str
