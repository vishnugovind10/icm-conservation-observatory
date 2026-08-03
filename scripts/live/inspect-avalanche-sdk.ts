import * as client from "@avalanche-sdk/client";
import * as clientAccounts from "@avalanche-sdk/client/accounts";
import * as clientChains from "@avalanche-sdk/client/chains";
import * as interchain from "@avalanche-sdk/interchain";
import * as interchainChains from "@avalanche-sdk/interchain/chains";

function exported(module: Record<string, unknown>) {
  return Object.keys(module).sort();
}

console.log(JSON.stringify({
  client: exported(client),
  clientAccounts: exported(clientAccounts),
  clientChains: exported(clientChains),
  interchain: exported(interchain),
  interchainChains: exported(interchainChains)
}, null, 2));
