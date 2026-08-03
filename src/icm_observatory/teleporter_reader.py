from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TeleporterMessageStatus:
    message_id: str
    source_chain: str
    destination_chain: str
    delivered: bool
    block_height: int | None = None


def normalize_status(message_id: str, source_chain: str, destination_chain: str, delivered: bool) -> TeleporterMessageStatus:
    return TeleporterMessageStatus(
        message_id=message_id,
        source_chain=source_chain,
        destination_chain=destination_chain,
        delivered=delivered,
    )
