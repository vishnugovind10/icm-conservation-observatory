<h1 align="center">ICM Conservation Observatory</h1>

<p align="center">
  <b>Continuous verification that Avalanche cross-chain bridges still balance.</b><br>
  Every ICTT bridge locks collateral on a home chain and mints a representation on remote chains.
  This tool checks that those two numbers still match, and tells you when they do not.
</p>

<p align="center">
  <a href="web/index.html"><b>Local Demo - Fuji fixture</b></a> |
  <a href="#what-it-detects">What It Detects</a> |
  <a href="#run-it-yourself">Run It Yourself</a> |
  <a href="PRIOR_ART.md">Why This Does Not Already Exist</a> |
  <a href="LIMITATIONS.md">Limitations</a>
</p>

> Status: open-source public template. The core invariant, classifier, read-only boundary, deterministic evidence bundle, and config-driven Fuji RPC reader are implemented. A real reference ICTT deployment config and hosted live demo are required before using it as live monitoring evidence.

## The Problem in Two Sentences

Avalanche Interchain Token Transfer locks collateral on a home chain and mints a matching supply on remote chains, coordinated by asynchronously relayed messages. Nothing today continuously verifies that locked collateral still equals total minted supply, so if that invariant breaks, the first signal is usually the incident, not a metric.

## What It Detects

| Classification | Meaning | Alert |
|---|---|---|
| `reconciled` | Locked collateral matches minted supply | none |
| `in_flight` | Gap fully explained by messages within normal relay time | none |
| `fallback_held` | Gap explained by a `sendAndCall` fallback recipient | info |
| `multi_hop` | Gap explained by an intermediate multi-hop state | info |
| `stale` | Gap persists past the observed relay baseline threshold | warning |
| `anomalous` | Gap explained by nothing: no pending message, no fallback, no multi-hop | critical |
| `unverifiable` | RPC degraded: state genuinely unknown, not assumed fine | warning |

The middle rows are the point. A monitor that flags every legitimate `sendAndCall` fallback as an anomaly gets muted quickly. Suppressing structural false positives is core logic, not polish.

## Run It Yourself

```bash
git clone https://github.com/vishnugovind10/icm-conservation-observatory
cd icm-conservation-observatory
python -m pip install -r requirements.txt

pytest
python -m icm_observatory.cli --fixture tests/fixtures/anomalous.json --evidence-dir artifacts/evidence
python scripts/export_static_demo.py
python scripts/package_static_demo.py
.\scripts\check-live-readiness.ps1 -Config config/fuji.example.json
uvicorn api.server:app --reload
```

No wallet. No keys. No signup. The default implementation is fixture-backed so tests require no network access.

## Live Fuji Mode

Copy `config/fuji.example.json`, replace the placeholder blockchain ID and contract addresses with a real ICTT deployment, then run:

```bash
set ICM_OBSERVATORY_CONFIG=config/fuji.local.json
python -m icm_observatory.cli --config config/fuji.local.json --evidence-dir artifacts/evidence
uvicorn api.server:app --reload
```

The Fuji C-Chain default is `https://api.avax-test.network/ext/bc/C/rpc` with EVM chain ID `43113`. Avalanche L1 EVM RPC URLs use `/ext/bc/[blockchainID]/rpc`.

The live reader fails closed. If any configured chain RPC is unhealthy or any read call fails, the result is `unverifiable`, not `anomalous`.

Supplemental observations can be included when pending messages, fallback holdings, or multi-hop state have been independently derived:

```bash
python -m icm_observatory.cli --fixture tests/fixtures/anomalous.json --observations examples/observations.in-flight.example.json
python scripts/package_static_demo.py --observations examples/observations.in-flight.example.json
```

Those observations are validated before classification and written into `correlation.json` so reviewers can inspect what was used to explain a gap. Invalid chain IDs, duplicate IDs, invalid addresses, negative ages, or nonpositive amounts fail before a result is emitted.

Evidence bundles include an `observation_summary` in `correlation.json`, so absence of supplemental observations is explicit rather than implied.

## Live Readiness Gate

Run:

```bash
./scripts/check-live-readiness.sh config/fuji.local.json https://YOUR_DEMO_URL
```

The command must pass before presenting the package as a live public deployment. It checks that the live config is Fuji, RPC URLs and contract addresses are non-placeholder, the static demo evidence is exported, the demo shows an anomalous divergence, and a public HTTPS demo URL is supplied.

For final public evidence, run the live bytecode check as well:

```bash
./scripts/check-live-readiness.sh config/fuji.local.json https://YOUR_DEMO_URL --live-verify
```

That option uses read-only `eth_getCode` calls to prove configured token home/remote addresses contain contract bytecode.

Official ICM contract address references currently identify the canonical Fuji C-Chain `TeleporterRegistry` and universal `TeleporterMessenger`; ICTT token home/remote deployment addresses remain deployment-specific and must be supplied in `config/fuji.local.json`.

## Static Demo Package

Run:

```bash
python scripts/package_static_demo.py
```

This writes `public/`, a static hosting artifact containing `index.html`, `demo-data/*`, and `deployment-manifest.json`. The manifest deliberately marks the package as not live-demo-ready because it uses deterministic fixture data. Replace it with live Fuji output and a public URL before presenting it as live evidence.

For the live path:

```bash
python scripts/package_static_demo.py --config config/fuji.local.json --public-demo-url https://YOUR_DEMO_URL
```

That command uses the read-only live RPC snapshot builder, writes the same static artifact shape, and embeds the readiness report in `public/deployment-manifest.json`.

GitHub Pages deployment notes are in [DEPLOYMENT.md](DEPLOYMENT.md). The included Pages workflow publishes the static fixture demo only; it does not make the package live-demo-ready.

## Safety Properties

- Read-only by construction. RPC access is allowlisted and tests fail if signing-related code paths are introduced.
- Fuji Testnet by default. Mainnet support must be explicit, opt-in, and user-supplied.
- No Ava Labs source code redistributed. The project is an independent companion and uses public ABI call shapes only.

## Honest Boundaries

Read [ASSUMPTIONS.md](ASSUMPTIONS.md) and [LIMITATIONS.md](LIMITATIONS.md) before trusting any output. An `anomalous` classification is a flag for investigation, not a confirmed vulnerability. This is independent, unaffiliated with Ava Labs, and is not an audit or security guarantee.

Public repo hygiene files are included for reviewer diligence: [SECURITY.md](SECURITY.md), [CONTRIBUTING.md](CONTRIBUTING.md), [LIMITATIONS.md](LIMITATIONS.md), and [CITATION.cff](CITATION.cff).

## License

Apache-2.0. Targets Avalanche Fuji Testnet by default in accordance with the project scope.
