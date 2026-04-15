from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from sqlalchemy.orm import Session

from app.core.event_manager import EventManager
from app.core.events import DispatchFailed, DispatchSucceeded
from app.models.orm import EventRecord, Rule
from app.models.repositories.channel_repository import ChannelRepository
from app.models.repositories.rule_repository import RuleRepository
from app.models.services.dispatcher_service import DispatcherService


@dataclass
class RouterContext:
    event:         EventRecord
    payload:       dict
    db:            Session
    dispatcher:    DispatcherService
    events:        EventManager
    matched_rules: list[Rule] = field(default_factory=list)
    results:       list[dict] = field(default_factory=list)


class PipelineStep(Protocol):
    async def execute(self, ctx: RouterContext) -> None:
        ...


class RuleMatchStep:
    async def execute(self, ctx: RouterContext) -> None:
        ctx.matched_rules = RuleRepository.match_all(
            ctx.db,
            source=ctx.event.source,
            event_type=ctx.event.event_type,
            payload=ctx.payload,
        )


class DispatchStep:
    async def execute(self, ctx: RouterContext) -> None:
        for rule in ctx.matched_rules:
            channel = ChannelRepository.get(ctx.db, rule.channel_id)
            if channel is None:
                ctx.results.append({
                    "rule_id":    rule.id,
                    "channel_id": rule.channel_id,
                    "status":     "failed",
                    "info":       "channel not found",
                })
                ctx.events.emit(DispatchFailed(
                    event_id=ctx.event.id,
                    rule_id=rule.id,
                    channel_id=rule.channel_id,
                    channel_type="unknown",
                    error="channel not found",
                ))
                continue

            success, info = await ctx.dispatcher.send(channel, ctx.event, ctx.payload)

            ctx.results.append({
                "rule_id":      rule.id,
                "channel_id":   channel.id,
                "channel_type": channel.type,
                "status":       "success" if success else "failed",
                "info":         info,
            })

            if success:
                ctx.events.emit(DispatchSucceeded(
                    event_id=ctx.event.id,
                    rule_id=rule.id,
                    channel_id=channel.id,
                    channel_type=channel.type,
                ))
            else:
                ctx.events.emit(DispatchFailed(
                    event_id=ctx.event.id,
                    rule_id=rule.id,
                    channel_id=channel.id,
                    channel_type=channel.type,
                    error=info,
                ))


class RouterPipeline:
    def __init__(self, steps: list[PipelineStep]) -> None:
        self._steps = steps

    async def run(self, ctx: RouterContext) -> list[dict]:
        for step in self._steps:
            await step.execute(ctx)
        return ctx.results
