# Live Demo Gate

Do not mark `ready_for_public_live_demo` as `true` until all four checks are real:

- Reference ICTT contracts are deployed on Fuji.
- The deployment has real transfer activity.
- A deliberate live divergence is visible to the observatory.
- The public HTTPS demo renders that live divergence.

## SDK Route

The current public Avalanche SDK docs use:

```bash
npm install @avalanche-sdk/interchain @avalanche-sdk/client viem
```

The repo pins those packages in `package.json` because the Interchain SDK is currently alpha-versioned and package names have changed over time.

## Secret Boundary

Set the deployer key only in the local shell, then run the guard:

```powershell
npm run live:check-env
```

Never write deployer keys, mnemonics, funded addresses, or private deployment notes into this repository.

## Required Live Inputs

Create `config/fuji.local.json` locally from `config/fuji.example.json` after deployment. It must include:

- Fuji C-Chain RPC URL.
- Remote Fuji L1 RPC URL.
- Collateral ERC-20 address.
- ICTT home or lock contract address.
- ICTT remote token contract address.

The local config is intentionally not committed.

## Gate Command

After live activity exists and the public demo URL has been deployed from live output:

```powershell
.\scripts\check-live-readiness.ps1 -Config config\fuji.local.json -PublicDemoUrl https://vishnugovind10.github.io/icm-conservation-observatory/ -LiveVerify
```

Only a passing result should allow a manifest with `ready_for_public_live_demo: true`.
