import os

import pytest

from icm_observatory.chain_client import FUJI_C_CHAIN_RPC_URL, JsonRpcClient


@pytest.mark.live
def test_fuji_public_rpc_chain_id_and_block_height():
    if os.environ.get("ICM_LIVE_TESTS") != "1":
        pytest.skip("set ICM_LIVE_TESTS=1 to run live Fuji RPC smoke")
    client = JsonRpcClient(FUJI_C_CHAIN_RPC_URL, timeout_seconds=15)
    assert client.chain_id() == 43113
    assert client.block_number() > 0
