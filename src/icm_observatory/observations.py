from __future__ import annotations

import json
import re
from dataclasses import replace
from pathlib import Path

from .models import DeploymentSnapshot, FallbackHolding, MultiHopState, PendingMessage

ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")


class ObservationValidationError(ValueError):
    pass


def load_observations(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _known_chains(snapshot: DeploymentSnapshot) -> set[str]:
    return {snapshot.home_chain.chain_id, *[chain.chain_id for chain in snapshot.remote_chains]}


def _require_positive_int(value: object, field: str, errors: list[str]) -> None:
    if not isinstance(value, int) or value <= 0:
        errors.append(f"{field} must be a positive integer")


def _require_nonnegative_int(value: object, field: str, errors: list[str]) -> None:
    if not isinstance(value, int) or value < 0:
        errors.append(f"{field} must be a nonnegative integer")


def validate_observations(snapshot: DeploymentSnapshot, payload: dict) -> None:
    errors: list[str] = []
    chains = _known_chains(snapshot)
    pending_ids: set[str] = set()
    fallback_ids: set[str] = set()
    transfer_ids: set[str] = set()

    for index, message in enumerate(payload.get("pending_messages", [])):
        prefix = f"pending_messages[{index}]"
        message_id = message.get("message_id")
        if not message_id:
            errors.append(f"{prefix}.message_id is required")
        elif message_id in pending_ids:
            errors.append(f"{prefix}.message_id duplicates {message_id}")
        else:
            pending_ids.add(message_id)
        if message.get("source_chain") not in chains:
            errors.append(f"{prefix}.source_chain is not in snapshot chains")
        if message.get("destination_chain") not in chains:
            errors.append(f"{prefix}.destination_chain is not in snapshot chains")
        _require_positive_int(message.get("amount"), f"{prefix}.amount", errors)
        _require_nonnegative_int(message.get("age_seconds"), f"{prefix}.age_seconds", errors)
        route = tuple(message.get("route", ()))
        if route and any(chain not in chains for chain in route):
            errors.append(f"{prefix}.route contains unknown chain")

    for index, holding in enumerate(payload.get("fallback_holdings", [])):
        prefix = f"fallback_holdings[{index}]"
        message_id = holding.get("message_id")
        if not message_id:
            errors.append(f"{prefix}.message_id is required")
        elif message_id in fallback_ids:
            errors.append(f"{prefix}.message_id duplicates {message_id}")
        else:
            fallback_ids.add(message_id)
        if holding.get("chain_id") not in chains:
            errors.append(f"{prefix}.chain_id is not in snapshot chains")
        recipient = holding.get("recipient")
        if not isinstance(recipient, str) or not ADDRESS_RE.fullmatch(recipient):
            errors.append(f"{prefix}.recipient must be a 20-byte hex address")
        _require_positive_int(holding.get("amount"), f"{prefix}.amount", errors)

    for index, state in enumerate(payload.get("multi_hop_states", [])):
        prefix = f"multi_hop_states[{index}]"
        transfer_id = state.get("transfer_id")
        if not transfer_id:
            errors.append(f"{prefix}.transfer_id is required")
        elif transfer_id in transfer_ids:
            errors.append(f"{prefix}.transfer_id duplicates {transfer_id}")
        else:
            transfer_ids.add(transfer_id)
        route = tuple(state.get("route", ()))
        if len(route) < 2:
            errors.append(f"{prefix}.route must contain at least two chains")
        elif any(chain not in chains for chain in route):
            errors.append(f"{prefix}.route contains unknown chain")
        _require_positive_int(state.get("amount"), f"{prefix}.amount", errors)
        hop = state.get("current_hop_index")
        _require_nonnegative_int(hop, f"{prefix}.current_hop_index", errors)
        if isinstance(hop, int) and route and hop >= len(route):
            errors.append(f"{prefix}.current_hop_index must be within route")

    if errors:
        raise ObservationValidationError("; ".join(errors))


def apply_observations(snapshot: DeploymentSnapshot, payload: dict) -> DeploymentSnapshot:
    validate_observations(snapshot, payload)
    return replace(
        snapshot,
        pending_messages=tuple(PendingMessage(**message) for message in payload.get("pending_messages", [])),
        fallback_holdings=tuple(FallbackHolding(**holding) for holding in payload.get("fallback_holdings", [])),
        multi_hop_states=tuple(MultiHopState(**state) for state in payload.get("multi_hop_states", [])),
        metadata={
            **snapshot.metadata,
            "observations_source": payload.get("source", "supplemental_observations"),
            "observations_note": payload.get("note", ""),
        },
    )


def apply_observations_file(snapshot: DeploymentSnapshot, path: Path | None) -> DeploymentSnapshot:
    if path is None:
        return snapshot
    return apply_observations(snapshot, load_observations(path))
