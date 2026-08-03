import { mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { createPublicClient, createWalletClient, formatEther, http, type Address } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { createICTTClient } from "@avalanche-sdk/interchain";
import { avalancheFuji, dispatch } from "@avalanche-sdk/interchain/chains";

const FUJI_C_CHAIN_RPC = process.env.FUJI_C_CHAIN_RPC_URL || "https://api.avax-test.network/ext/bc/C/rpc";
const DISPATCH_RPC = process.env.DISPATCH_RPC_URL || "https://subnets.avax.network/dispatch/testnet/rpc";
const OUTPUT_PATH = process.env.ICTT_DEPLOYMENT_OUTPUT || "artifacts/live/fuji-ictt-deployment.json";
const CONFIG_OUTPUT_PATH = process.env.ICM_OBSERVATORY_LIVE_CONFIG || "config/fuji.local.generated.json";
const INITIAL_SUPPLY = Number(process.env.ICTT_INITIAL_SUPPLY || "1000000");
const TRANSFER_AMOUNT = Number(process.env.ICTT_TRANSFER_AMOUNT || "1");

function requiredPrivateKey(): `0x${string}` {
  const key = process.env.FUJI_DEPLOYER_KEY;
  if (!key) {
    throw new Error("FUJI_DEPLOYER_KEY is required and must stay out of committed files.");
  }
  if (!/^0x[0-9a-fA-F]{64}$/.test(key)) {
    throw new Error("FUJI_DEPLOYER_KEY must be a 0x-prefixed 32-byte private key.");
  }
  return key as `0x${string}`;
}

async function assertFunded(label: string, balance: bigint) {
  if (balance === 0n) {
    throw new Error(`${label} balance is zero. Fund the deployer on this chain before running live deployment.`);
  }
}

async function writeJson(path: string, value: unknown) {
  const absolute = resolve(path);
  await mkdir(dirname(absolute), { recursive: true });
  await writeFile(absolute, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

async function main() {
  const account = privateKeyToAccount(requiredPrivateKey());
  const sourceChain = {
    ...avalancheFuji,
    rpcUrls: { default: { http: [FUJI_C_CHAIN_RPC] } },
  };
  const destinationChain = {
    ...dispatch,
    rpcUrls: { default: { http: [DISPATCH_RPC] } },
  };

  const fujiPublic = createPublicClient({ chain: sourceChain, transport: http(FUJI_C_CHAIN_RPC) });
  const dispatchPublic = createPublicClient({ chain: destinationChain, transport: http(DISPATCH_RPC) });
  const fujiWallet = createWalletClient({ chain: sourceChain, transport: http(FUJI_C_CHAIN_RPC), account });
  const dispatchWallet = createWalletClient({ chain: destinationChain, transport: http(DISPATCH_RPC), account });

  const [fujiBalance, dispatchBalance] = await Promise.all([
    fujiPublic.getBalance({ address: account.address }),
    dispatchPublic.getBalance({ address: account.address }),
  ]);
  await assertFunded("Fuji C-Chain", fujiBalance);
  await assertFunded("Dispatch Fuji L1", dispatchBalance);

  const ictt = createICTTClient(sourceChain, destinationChain);
  const deployment: Record<string, unknown> = {
    deployer: account.address,
    sourceChain: {
      name: sourceChain.name,
      chainId: sourceChain.id,
      blockchainId: sourceChain.blockchainId,
      rpcUrl: FUJI_C_CHAIN_RPC,
      balance: formatEther(fujiBalance),
    },
    destinationChain: {
      name: destinationChain.name,
      chainId: destinationChain.id,
      blockchainId: destinationChain.blockchainId,
      rpcUrl: DISPATCH_RPC,
      balance: formatEther(dispatchBalance),
    },
    transactions: {},
  };

  console.log(`deployer=${account.address}`);
  console.log(`fuji_balance=${formatEther(fujiBalance)}`);
  console.log(`dispatch_balance=${formatEther(dispatchBalance)}`);

  const token = await ictt.deployERC20Token({
    walletClient: fujiWallet,
    sourceChain,
    name: "ICM Observatory Test Token",
    symbol: "ICMOBS",
    initialSupply: INITIAL_SUPPLY,
    recipient: account.address,
  });
  deployment.collateralToken = token.contractAddress;
  deployment.transactions = { ...deployment.transactions, deployToken: token.txHash };
  await writeJson(OUTPUT_PATH, deployment);
  console.log(`collateral_token=${token.contractAddress}`);

  const home = await ictt.deployTokenHomeContract({
    walletClient: fujiWallet,
    sourceChain,
    erc20TokenAddress: token.contractAddress,
    minimumTeleporterVersion: 1,
  });
  deployment.homeContract = home.contractAddress;
  deployment.transactions = { ...deployment.transactions, deployHome: home.txHash };
  await writeJson(OUTPUT_PATH, deployment);
  console.log(`home_contract=${home.contractAddress}`);

  const remote = await ictt.deployTokenRemoteContract({
    walletClient: dispatchWallet,
    sourceChain,
    destinationChain,
    tokenHomeContract: home.contractAddress,
  });
  deployment.remoteContract = remote.contractAddress;
  deployment.transactions = { ...deployment.transactions, deployRemote: remote.txHash };
  await writeJson(OUTPUT_PATH, deployment);
  console.log(`remote_contract=${remote.contractAddress}`);

  const registration = await ictt.registerRemoteWithHome({
    walletClient: dispatchWallet,
    sourceChain,
    destinationChain,
    tokenRemoteContract: remote.contractAddress,
  });
  deployment.transactions = { ...deployment.transactions, registerRemoteWithHome: registration.txHash };
  await writeJson(OUTPUT_PATH, deployment);
  console.log(`register_remote_tx=${registration.txHash}`);

  const approval = await ictt.approveToken({
    walletClient: fujiWallet,
    sourceChain,
    tokenHomeContract: home.contractAddress,
    tokenAddress: token.contractAddress,
    amountInBaseUnit: TRANSFER_AMOUNT,
  });
  deployment.transactions = { ...deployment.transactions, approveToken: approval.txHash };
  await writeJson(OUTPUT_PATH, deployment);
  console.log(`approve_tx=${approval.txHash}`);

  const transfer = await ictt.sendToken({
    walletClient: fujiWallet,
    sourceChain,
    destinationChain,
    tokenHomeContract: home.contractAddress,
    tokenRemoteContract: remote.contractAddress,
    recipient: account.address as Address,
    amountInBaseUnit: TRANSFER_AMOUNT,
  });
  deployment.transactions = { ...deployment.transactions, sendToken: transfer.txHash };
  deployment.transferAmount = TRANSFER_AMOUNT;
  await writeJson(OUTPUT_PATH, deployment);
  console.log(`send_token_tx=${transfer.txHash}`);

  await writeJson(CONFIG_OUTPUT_PATH, {
    network: "fuji",
    chains: {
      "fuji-c-chain": {
        name: "Avalanche Fuji C-Chain",
        rpc_url: FUJI_C_CHAIN_RPC,
        expected_evm_chain_id: 43113,
      },
      "dispatch-fuji": {
        name: "Dispatch Fuji L1",
        rpc_url: DISPATCH_RPC,
        expected_evm_chain_id: destinationChain.id,
      },
    },
    deployments: [
      {
        deployment_id: "fuji-dispatch-live-ictt",
        home: {
          chain_id: "fuji-c-chain",
          collateral_token: token.contractAddress,
          lock_contract: home.contractAddress,
        },
        remotes: [
          {
            chain_id: "dispatch-fuji",
            token_contract: remote.contractAddress,
          },
        ],
        tolerance: 0,
        stale_threshold_seconds: 180,
      },
    ],
  });
  console.log(`deployment_output=${OUTPUT_PATH}`);
  console.log(`observatory_config=${CONFIG_OUTPUT_PATH}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
