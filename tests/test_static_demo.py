import json
import subprocess
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.request import urlopen
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_DATA = PROJECT_ROOT / "web" / "demo-data"
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))


def test_static_demo_export_matches_divergence_fixture():
    subprocess.run([sys.executable, "scripts/export_static_demo.py"], cwd=PROJECT_ROOT, check=True)
    conservation = json.loads((DEMO_DATA / "conservation.json").read_text(encoding="utf-8"))
    merkle = json.loads((DEMO_DATA / "merkle.json").read_text(encoding="utf-8"))
    manifest = json.loads((DEMO_DATA / "manifest.json").read_text(encoding="utf-8"))

    assert conservation["classification"] == "anomalous"
    assert conservation["unexplained_gap"] == 15000
    assert manifest["merkle_root"] == merkle["root"]
    assert "EXCEPTIONS.md" in manifest["files"]


def test_static_demo_html_loads_exported_evidence_files():
    html = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
    for path in [
        "demo-data/bundle.json",
        "demo-data/conservation.json",
        "demo-data/correlation.json",
        "demo-data/EXCEPTIONS.md",
        "demo-data/merkle.json",
        "demo-data/manifest.json",
    ]:
        assert path in html


def test_static_demo_package_is_hostable():
    subprocess.run([sys.executable, "scripts/package_static_demo.py"], cwd=PROJECT_ROOT, check=True)
    public = PROJECT_ROOT / "public"
    assert (public / "index.html").exists()
    assert (public / "demo-data" / "conservation.json").exists()
    deployment = json.loads((public / "deployment-manifest.json").read_text(encoding="utf-8"))
    conservation = json.loads((public / "demo-data" / "conservation.json").read_text(encoding="utf-8"))
    assert deployment["ready_for_public_live_demo"] is False
    assert deployment["readiness"]["ready"] is False
    assert deployment["evidence_root"] == json.loads((public / "demo-data" / "merkle.json").read_text())["root"]
    assert conservation["classification"] == "anomalous"


def test_packaged_static_demo_serves_over_http():
    subprocess.run([sys.executable, "scripts/package_static_demo.py"], cwd=PROJECT_ROOT, check=True)
    public = PROJECT_ROOT / "public"
    handler = partial(SimpleHTTPRequestHandler, directory=str(public))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        with urlopen(base + "/index.html", timeout=5) as response:
            assert response.status == 200
        with urlopen(base + "/demo-data/conservation.json", timeout=5) as response:
            assert response.status == 200
            assert json.loads(response.read().decode("utf-8"))["unexplained_gap"] == 15000
    finally:
        server.shutdown()
        server.server_close()


def test_live_package_manifest_can_be_live_ready_with_valid_inputs(tmp_path, monkeypatch):
    import package_static_demo

    monkeypatch.setattr(package_static_demo, "PUBLIC_ROOT", tmp_path / "public-ready")

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
    fixture_snapshot = package_static_demo.load_snapshot(PROJECT_ROOT / "tests" / "fixtures" / "anomalous.json")
    with patch.object(package_static_demo, "build_live_snapshot", return_value=fixture_snapshot):
        manifest = package_static_demo.package_demo(
            config_path=config_path,
            public_demo_url="https://example.com/icm-conservation-observatory",
        )
    assert manifest["mode"] == "live-rpc-demo"
    assert manifest["network"] == "fuji"
    assert manifest["ready_for_public_live_demo"] is True
    assert manifest["readiness"]["ready"] is True


def test_live_package_manifest_stays_not_ready_without_public_url(tmp_path, monkeypatch):
    import package_static_demo

    monkeypatch.setattr(package_static_demo, "PUBLIC_ROOT", tmp_path / "public-not-ready")

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
    fixture_snapshot = package_static_demo.load_snapshot(PROJECT_ROOT / "tests" / "fixtures" / "anomalous.json")
    with patch.object(package_static_demo, "build_live_snapshot", return_value=fixture_snapshot):
        manifest = package_static_demo.package_demo(config_path=config_path)
    assert manifest["ready_for_public_live_demo"] is False
    assert manifest["readiness"]["ready"] is False
