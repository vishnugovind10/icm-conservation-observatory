from __future__ import annotations

from dataclasses import dataclass

from .models import PendingMessage


@dataclass(frozen=True)
class CorrelationResult:
    matched_message_ids: tuple[str, ...]
    pending_messages: tuple[PendingMessage, ...]


def correlate_messages(sent_ids: set[str], received_ids: set[str], pending: tuple[PendingMessage, ...]) -> CorrelationResult:
    matched = tuple(sorted(sent_ids & received_ids))
    known_pending = tuple(message for message in pending if message.message_id in sent_ids - received_ids)
    return CorrelationResult(matched_message_ids=matched, pending_messages=known_pending)
