import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from icm_observatory.config import load_config
from icm_observatory.readiness import build_readiness_report, verify_contract_code


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def ensure_default_demo_data() -> None:
    subprocess.run([sys.executable, "scripts/export_static_demo.py"], cwd=PROJECT_ROOT, check=True)


def test_example_config_is_not_live_ready():
    ensure_default_demo_data()
    report = build_readiness_report(
        config_path=PROJECT_ROOT / "config" / "fuji.example.json",
        demo_data=PROJECT_ROOT / "web" / "demo-data",
        public_demo_url=None,
    )
    assert report.ready is False
    failures = {check.name: check.detail for check in report.checks if check.status == "fail"}
    assert "contract_addresses_configured" in failures
    assert "public_demo_url" in failures


def test_valid_config_and_public_url_can_pass_readiness(tmp_path):
    ensure_default_demo_data()
    config_path = tmp_path / "fuji.live.json"
    config_path.write_text(
        json.dumps(
            {
                "network": "fuji",
                "chains": {
                    "fuji-c-chain": {
                        "name": "Avalanche Fuji C-Chain",
                        "rpc_url": "https://api.avax-test.network/ext/bc/C/rpc",
                        "expected_evm_chain_id": 43113,
                    },
                    "fuji-l1": {
                        "name": "Fuji L1",
                        "rpc_url": "https://api.avax-test.network/ext/bc/example/rpc",
                    },
                },
                "deployments": [
                    {
                        "deployment_id": "live-demo",
                        "home": {
                            "chain_id": "fuji-c-chain",
                            "collateral_token": "0x1111111111111111111111111111111111111111",
                            "lock_contract": "0x2222222222222222222222222222222222222222",
                        },
                        "remotes": [
                            {
                                "chain_id": "fuji-l1",
                                "token_contract": "0x3333333333333333333333333333333333333333",
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    report = build_readiness_report(
        config_path=config_path,
        demo_data=PROJECT_ROOT / "web" / "demo-data",
        public_demo_url="https://example.com/icm-conservation-observatory",
    )
    assert report.ready is True


class FakeCodeClient:
    def __init__(self, url: str, code: str = "0x6000"):
        self.url = url
        self.code = code

    def call(self, method, params=None):
        assert method == "eth_getCode"
        return self.code


def write_valid_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "fuji.live.json"
    config_path.write_text(
        json.dumps(
            {
                "network": "fuji",
                "chains": {
                    "fuji-c-chain": {
                        "name": "Avalanche Fuji C-Chain",
                        "rpc_url": "https://api.avax-test.network/ext/bc/C/rpc",
                        "expected_evm_chain_id": 43113,
                    }
                },
                "deployments": [
                    {
                        "deployment_id": "live-demo",
                        "home": {
                            "chain_id": "fuji-c-chain",
                            "collateral_token": "0x1111111111111111111111111111111111111111",
                            "lock_contract": "0x2222222222222222222222222222222222222222",
                        },
                        "remotes": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return config_path


def test_live_contract_code_verification_passes_when_bytecode_exists(tmp_path):
    config = load_config(write_valid_config(tmp_path))
    with patch("icm_observatory.readiness.JsonRpcClient", lambda url: FakeCodeClient(url, "0x6000")):
        checks = verify_contract_code(config)
    assert checks[0].status == "pass"
    assert "2 contract" in checks[0].detail


def test_live_contract_code_verification_fails_on_empty_code(tmp_path):
    config = load_config(write_valid_config(tmp_path))
    with patch("icm_observatory.readiness.JsonRpcClient", lambda url: FakeCodeClient(url, "0x")):
        checks = verify_contract_code(config)
    assert checks[0].status == "fail"
    assert "no contract code" in checks[0].detail


def test_readiness_live_verify_includes_contract_code_check(tmp_path):
    ensure_default_demo_data()
    config_path = write_valid_config(tmp_path)
    with patch("icm_observatory.readiness.JsonRpcClient", lambda url: FakeCodeClient(url, "0x6000")):
        report = build_readiness_report(
            config_path=config_path,
            demo_data=PROJECT_ROOT / "web" / "demo-data",
            public_demo_url="https://example.com/icm-conservation-observatory",
            live_verify=True,
        )
    assert report.ready is True
    assert any(check.name == "live_contract_code" and check.status == "pass" for check in report.checks)
