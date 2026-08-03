from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


READ_ONLY_RPC_METHODS = frozenset(
    {
        "eth_blockNumber",
        "eth_call",
        "eth_chainId",
        "eth_getBalance",
        "eth_getBlockByNumber",
        "eth_getCode",
        "eth_getLogs",
        "eth_getStorageAt",
        "eth_getTransactionReceipt",
    }
)

FUJI_C_CHAIN_RPC_URL = "https://api.avax-test.network/ext/bc/C/rpc"
FUJI_C_CHAIN_ID_HEX = "0xa869"


class ReadOnlyRpcError(RuntimeError):
    pass


@dataclass(frozen=True)
class JsonRpcClient:
    url: str
    timeout_seconds: int = 10

    def call(self, method: str, params: list[Any] | None = None) -> Any:
        if method not in READ_ONLY_RPC_METHODS:
            raise ReadOnlyRpcError(f"RPC method is outside the read-only allowlist: {method}")
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []}).encode("utf-8")
        request = urllib.request.Request(
            self.url,
            data=body,
            headers={"content-type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ReadOnlyRpcError(f"RPC call failed for {method}: {exc}") from exc
        if "error" in payload:
            raise ReadOnlyRpcError(str(payload["error"]))
        return payload["result"]

    def block_number(self) -> int:
        return int(self.call("eth_blockNumber"), 16)

    def chain_id(self) -> int:
        return int(self.call("eth_chainId"), 16)

    def healthy(self, expected_chain_id: int | None = None) -> bool:
        try:
            actual_chain_id = self.chain_id()
            self.block_number()
        except ReadOnlyRpcError:
            return False
        return expected_chain_id is None or actual_chain_id == expected_chain_id
