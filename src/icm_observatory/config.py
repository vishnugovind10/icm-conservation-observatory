from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .chain_client import FUJI_C_CHAIN_RPC_URL


@dataclass(frozen=True)
class ChainConfig:
    chain_id: str
    name: str
    rpc_url: str
    expected_evm_chain_id: int | None = None


@dataclass(frozen=True)
class HomeConfig:
    chain_id: str
    collateral_token: str
    lock_contract: str


@dataclass(frozen=True)
class RemoteConfig:
    chain_id: str
    token_contract: str


@dataclass(frozen=True)
class DeploymentConfig:
    deployment_id: str
    home: HomeConfig
    remotes: tuple[RemoteConfig, ...]
    tolerance: int = 0
    stale_threshold_seconds: int = 180


@dataclass(frozen=True)
class ObservatoryConfig:
    network: str
    chains: dict[str, ChainConfig]
    deployments: tuple[DeploymentConfig, ...]


def load_config(path: Path) -> ObservatoryConfig:
    payload = json.loads(path.read_text(encoding="utf-8"))
    chains = {
        chain_id: ChainConfig(
            chain_id=chain_id,
            name=chain_payload["name"],
            rpc_url=chain_payload.get("rpc_url") or FUJI_C_CHAIN_RPC_URL,
            expected_evm_chain_id=chain_payload.get("expected_evm_chain_id"),
        )
        for chain_id, chain_payload in payload.get("chains", {}).items()
    }
    deployments = tuple(
        DeploymentConfig(
            deployment_id=deployment["deployment_id"],
            home=HomeConfig(**deployment["home"]),
            remotes=tuple(RemoteConfig(**remote) for remote in deployment.get("remotes", [])),
            tolerance=int(deployment.get("tolerance", 0)),
            stale_threshold_seconds=int(deployment.get("stale_threshold_seconds", 180)),
        )
        for deployment in payload.get("deployments", [])
    )
    return ObservatoryConfig(network=payload.get("network", "fuji"), chains=chains, deployments=deployments)
