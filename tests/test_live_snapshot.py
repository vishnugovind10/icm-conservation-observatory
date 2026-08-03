from icm_observatory.config import ChainConfig, DeploymentConfig, HomeConfig, ObservatoryConfig, RemoteConfig
from icm_observatory.conservation import evaluate_conservation
from icm_observatory.live_snapshot import build_live_snapshot
from icm_observatory.models import Classification


class FakeClient:
    def __init__(self, url: str):
        self.url = url

    def healthy(self, expected_chain_id=None):
        return self.url != "unhealthy"

    def block_number(self):
        return 123

    def call(self, method, params=None):
        if method == "eth_call" and params[0]["data"].startswith("0x70a08231"):
            return hex(1000)
        if method == "eth_call" and params[0]["data"] == "0x18160ddd":
            return hex(1000)
        raise AssertionError(f"unexpected method in fake client: {method}")


def config_with_rpc(remote_rpc: str = "remote") -> tuple[ObservatoryConfig, DeploymentConfig]:
    config = ObservatoryConfig(
        network="fuji",
        chains={
            "home": ChainConfig("home", "Home", "home", 43113),
            "remote": ChainConfig("remote", "Remote", remote_rpc, None),
        },
        deployments=(
            DeploymentConfig(
                deployment_id="demo",
                home=HomeConfig(
                    chain_id="home",
                    collateral_token="0x1111111111111111111111111111111111111111",
                    lock_contract="0x2222222222222222222222222222222222222222",
                ),
                remotes=(
                    RemoteConfig(
                        chain_id="remote",
                        token_contract="0x3333333333333333333333333333333333333333",
                    ),
                ),
            ),
        ),
    )
    return config, config.deployments[0]


def test_live_snapshot_uses_read_only_contract_calls():
    config, deployment = config_with_rpc()
    snapshot = build_live_snapshot(config, deployment, client_factory=FakeClient)
    result = evaluate_conservation(snapshot, stale_threshold_seconds=180)
    assert result.classification == Classification.RECONCILED
    assert snapshot.metadata["source"] == "live_rpc"
    assert snapshot.home_chain.block_height == 123


def test_unhealthy_rpc_becomes_unverifiable():
    config, deployment = config_with_rpc(remote_rpc="unhealthy")
    snapshot = build_live_snapshot(config, deployment, client_factory=FakeClient)
    result = evaluate_conservation(snapshot, stale_threshold_seconds=180)
    assert result.classification == Classification.UNVERIFIABLE
    assert snapshot.metadata["rpc_health"]["remote"] is False
