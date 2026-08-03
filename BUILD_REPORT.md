# Build Report

Generated: 2026-08-03

## Implemented

- Read-only JSON-RPC allowlist.
- Config-driven Fuji live RPC snapshot reader.
- ERC-20 `totalSupply` and `balanceOf` read helpers for ICTT-style token accounting.
- Conservation equation evaluation.
- Classifier labels: `reconciled`, `in_flight`, `fallback_held`, `multi_hop`, `stale`, `anomalous`, `unverifiable`.
- Deterministic evidence bundle generation with Merkle root.
- Static local dashboard rendered from exported evidence bundle data.
- Static `public/` demo package with fixture and live-config modes.
- Live readiness checker for live config, evidence export, anomalous demo, and public URL.
- Optional live readiness verification that configured contract addresses contain bytecode via read-only `eth_getCode`.
- Supplemental observation import for pending messages, fallback holdings, and multi-hop state; observations are validated and included in evidence correlation output.
- Observation provenance summary in `correlation.json`, committed through the evidence Merkle root.
- FastAPI endpoints for `/conservation`, `/classification`, `/evidence`, and `/metrics`.
- Prometheus alert rule skeleton and Grafana dashboard skeleton.
- GitHub Actions CI workflow for offline tests, static packaging, readiness fail-closed check, and manual live Fuji smoke.
- GitHub Pages workflow for publishing the static fixture demo package.
- Public-release hygiene files: `SECURITY.md`, `CONTRIBUTING.md`, `LIMITATIONS.md`, `CITATION.cff`.

## Verified

```text
python -m pytest -q
42 passed, 1 skipped
```

```text
$env:ICM_LIVE_TESTS='1'; python -m pytest -q tests\live\test_fuji_rpc_smoke.py
1 passed
```

```text
.\scripts\run-observatory.ps1
classification: anomalous
locked_collateral: 1000000
total_minted_supply: 985000
unexplained_gap: 15000
```

Generated evidence files:

- `bundle.json`
- `conservation.json`
- `correlation.json`
- `EXCEPTIONS.md`
- `manifest.json` in `web/demo-data`
- `merkle.json`

Merkle root from the generated divergence bundle:

```text
dcd5cda5723d80e1751aec5c9ced5a0d8bb05d58ed6dbb0a014832f6cd9d7834
```

Determinism regression:

```text
Changing generated_at does not change the Merkle root.
bundle.json leaf commits to the manifest without generated_at.
```

Static demo HTTP check:

```text
index_status=200
data_status=200
classification: anomalous
unexplained_gap: 15000
```

Packaged static demo check:

```text
public/index.html: present
public/demo-data/conservation.json: present
public/deployment-manifest.json: ready_for_public_live_demo=false
packaged HTTP check: 200 for index and conservation data
mocked live package with valid config + HTTPS URL: ready_for_public_live_demo=true
```

Live readiness check against `config/fuji.example.json`:

```text
ready: false
expected blockers: placeholder L1 RPC URL, placeholder ICTT contract addresses, missing public HTTPS demo URL
live verify blocker: placeholder contract addresses cannot pass eth_getCode bytecode checks
exit code: 1
```

## Not Yet Complete

- Live Fuji RPC monitoring.
- Reference ICTT deployment configuration.
- Public hosted demo URL.
- `mapping/` reuse layer integration tests.
- Live screenshot of a deliberate Fuji divergence.
