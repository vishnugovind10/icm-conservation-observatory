import ast
from pathlib import Path

from icm_observatory.chain_client import JsonRpcClient, READ_ONLY_RPC_METHODS, ReadOnlyRpcError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"


def test_rpc_methods_are_allowlisted():
    client = JsonRpcClient("http://127.0.0.1:9650/ext/bc/C/rpc")
    try:
        client.call("eth_getTransactionCount")
    except ReadOnlyRpcError as exc:
        assert "outside the read-only allowlist" in str(exc)
    else:
        raise AssertionError("non-allowlisted RPC method was accepted")


def test_no_signing_imports_or_transaction_builders():
    forbidden_names = {
        "Account",
        "PrivateKey",
        "SigningKey",
        "Wallet",
        "sign_transaction",
        "send_transaction",
        "send_raw_transaction",
        "build_transaction",
    }
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                assert node.id not in forbidden_names, f"{path} uses forbidden name {node.id}"
            if isinstance(node, ast.Attribute):
                assert node.attr not in forbidden_names, f"{path} uses forbidden attribute {node.attr}"


def test_allowlist_contains_only_read_methods():
    assert all(method.startswith("eth_") for method in READ_ONLY_RPC_METHODS)
    assert "eth_call" in READ_ONLY_RPC_METHODS
    assert "eth_getLogs" in READ_ONLY_RPC_METHODS
