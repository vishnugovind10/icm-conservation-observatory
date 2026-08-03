import { privateKeyToAccount } from "viem/accounts";

const key = process.env.FUJI_DEPLOYER_KEY;
if (!key) {
  console.error("FUJI_DEPLOYER_KEY is required and must stay out of committed files.");
  process.exit(1);
}

if (!/^0x[0-9a-fA-F]{64}$/.test(key)) {
  console.error("FUJI_DEPLOYER_KEY must be a 0x-prefixed 32-byte private key.");
  process.exit(1);
}

const account = privateKeyToAccount(key);
console.log(JSON.stringify({ address: account.address }, null, 2));
