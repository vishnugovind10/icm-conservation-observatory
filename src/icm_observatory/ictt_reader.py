from __future__ import annotations

from .chain_client import JsonRpcClient


ERC20_TOTAL_SUPPLY_SELECTOR = "0x18160ddd"
ERC20_BALANCE_OF_SELECTOR = "0x70a08231"


def _address_arg(address: str) -> str:
    cleaned = address.lower().removeprefix("0x")
    if len(cleaned) != 40:
        raise ValueError("address must be a 20-byte hex string")
    return cleaned.rjust(64, "0")


def _hex_to_int(value: str) -> int:
    return int(value or "0x0", 16)


def read_total_supply(client: JsonRpcClient, token_contract: str, block: str = "latest") -> int:
    result = client.call("eth_call", [{"to": token_contract, "data": ERC20_TOTAL_SUPPLY_SELECTOR}, block])
    return _hex_to_int(result)


def read_balance_of(client: JsonRpcClient, token_contract: str, account: str, block: str = "latest") -> int:
    data = ERC20_BALANCE_OF_SELECTOR + _address_arg(account)
    result = client.call("eth_call", [{"to": token_contract, "data": data}, block])
    return _hex_to_int(result)
