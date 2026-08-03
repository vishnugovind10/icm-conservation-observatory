from pathlib import Path

from icm_observatory.config import load_config


def test_fuji_example_config_defaults_to_public_c_chain_rpc():
    config = load_config(Path("config/fuji.example.json"))
    assert config.network == "fuji"
    assert config.chains["fuji-c-chain"].expected_evm_chain_id == 43113
    assert config.deployments[0].stale_threshold_seconds == 180
