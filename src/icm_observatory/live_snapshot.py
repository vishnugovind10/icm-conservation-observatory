from __future__ import annotations

from collections.abc import Callable

from .chain_client import JsonRpcClient, ReadOnlyRpcError
from .config import DeploymentConfig, ObservatoryConfig
from .ictt_reader import read_balance_of, read_total_supply
from .models import ChainRef, DeploymentSnapshot

ClientFactory = Callable[[str], JsonRpcClient]


def _chain_ref(config: ObservatoryConfig, chain_id: str, client: JsonRpcClient | None, healthy: bool) -> ChainRef:
    chain = config.chains[chain_id]
    block_height = None
    if healthy and client is not None:
        try:
            block_height = client.block_number()
        except ReadOnlyRpcError:
            block_height = None
    return ChainRef(chain_id=chain.chain_id, name=chain.name, rpc_url=chain.rpc_url, block_height=block_height)


def build_live_snapshot(
    config: ObservatoryConfig,
    deployment: DeploymentConfig,
    client_factory: ClientFactory = JsonRpcClient,
) -> DeploymentSnapshot:
    clients: dict[str, JsonRpcClient] = {}
    health: dict[str, bool] = {}
    for chain_id in {deployment.home.chain_id, *[remote.chain_id for remote in deployment.remotes]}:
        chain = config.chains[chain_id]
        client = client_factory(chain.rpc_url)
        clients[chain_id] = client
        health[chain_id] = client.healthy(chain.expected_evm_chain_id)

    rpc_healthy = all(health.values())
    home_client = clients[deployment.home.chain_id]
    try:
        locked = (
            read_balance_of(home_client, deployment.home.collateral_token, deployment.home.lock_contract)
            if rpc_healthy
            else 0
        )
        minted = {
            remote.chain_id: read_total_supply(clients[remote.chain_id], remote.token_contract) if rpc_healthy else 0
            for remote in deployment.remotes
        }
    except (ReadOnlyRpcError, ValueError):
        rpc_healthy = False
        locked = 0
        minted = {remote.chain_id: 0 for remote in deployment.remotes}

    return DeploymentSnapshot(
        deployment_id=deployment.deployment_id,
        home_chain=_chain_ref(config, deployment.home.chain_id, home_client, health.get(deployment.home.chain_id, False)),
        remote_chains=tuple(
            _chain_ref(config, remote.chain_id, clients[remote.chain_id], health.get(remote.chain_id, False))
            for remote in deployment.remotes
        ),
        locked_collateral=locked,
        minted_supply=minted,
        rpc_healthy=rpc_healthy,
        tolerance=deployment.tolerance,
        metadata={
            "source": "live_rpc",
            "network": config.network,
            "rpc_health": health,
        },
    )
