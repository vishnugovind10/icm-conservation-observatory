from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Classification(StrEnum):
    RECONCILED = "reconciled"
    IN_FLIGHT = "in_flight"
    FALLBACK_HELD = "fallback_held"
    MULTI_HOP = "multi_hop"
    STALE = "stale"
    ANOMALOUS = "anomalous"
    UNVERIFIABLE = "unverifiable"


@dataclass(frozen=True)
class ChainRef:
    chain_id: str
    name: str
    rpc_url: str = ""
    block_height: int | None = None


@dataclass(frozen=True)
class PendingMessage:
    message_id: str
    source_chain: str
    destination_chain: str
    amount: int
    age_seconds: int
    status: str = "sent"
    route: tuple[str, ...] = ()


@dataclass(frozen=True)
class FallbackHolding:
    message_id: str
    chain_id: str
    recipient: str
    amount: int


@dataclass(frozen=True)
class MultiHopState:
    transfer_id: str
    route: tuple[str, ...]
    amount: int
    current_hop_index: int


@dataclass(frozen=True)
class DeploymentSnapshot:
    deployment_id: str
    home_chain: ChainRef
    remote_chains: tuple[ChainRef, ...]
    locked_collateral: int
    minted_supply: dict[str, int]
    pending_messages: tuple[PendingMessage, ...] = ()
    fallback_holdings: tuple[FallbackHolding, ...] = ()
    multi_hop_states: tuple[MultiHopState, ...] = ()
    rpc_healthy: bool = True
    tolerance: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConservationResult:
    deployment_id: str
    locked_collateral: int
    total_minted_supply: int
    pending_amount: int
    raw_gap: int
    unexplained_gap: int
    classification: Classification
    reason: str
    alert_level: str
