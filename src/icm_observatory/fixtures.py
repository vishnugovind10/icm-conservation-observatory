from __future__ import annotations

import json
from pathlib import Path

from .models import ChainRef, DeploymentSnapshot, FallbackHolding, MultiHopState, PendingMessage


def load_snapshot(path: Path) -> DeploymentSnapshot:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return snapshot_from_dict(payload)


def snapshot_from_dict(payload: dict) -> DeploymentSnapshot:
    return DeploymentSnapshot(
        deployment_id=payload["deployment_id"],
        home_chain=ChainRef(**payload["home_chain"]),
        remote_chains=tuple(ChainRef(**chain) for chain in payload.get("remote_chains", [])),
        locked_collateral=int(payload["locked_collateral"]),
        minted_supply={chain: int(amount) for chain, amount in payload.get("minted_supply", {}).items()},
        pending_messages=tuple(PendingMessage(**message) for message in payload.get("pending_messages", [])),
        fallback_holdings=tuple(FallbackHolding(**holding) for holding in payload.get("fallback_holdings", [])),
        multi_hop_states=tuple(MultiHopState(**state) for state in payload.get("multi_hop_states", [])),
        rpc_healthy=bool(payload.get("rpc_healthy", True)),
        tolerance=int(payload.get("tolerance", 0)),
        metadata=payload.get("metadata", {}),
    )
