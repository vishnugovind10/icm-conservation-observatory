# Architecture

The observatory is split into three layers:

1. Read-only data acquisition: `chain_client.py`, `ictt_reader.py`, `config.py`, `live_snapshot.py`, and future Teleporter log readers.
2. Conservation logic: `conservation.py`, `classifier.py`, `message_correlator.py`, and `relay_baseline.py`.
3. Reviewable outputs: `api/server.py`, `web/index.html`, and deterministic evidence bundles from `evidence.py`.

The invariant is:

```text
locked_collateral(home) == sum(minted_supply(remote_i)) + sum(in_flight(pending_messages))
```

The implementation deliberately separates `unverifiable` from `anomalous`. A degraded RPC source means the state is unknown; it is not proof of solvency or proof of breach.

## Current Build Slice

The current repo implements the public template proof:

- known-answer fixture evaluation;
- fallback and multi-hop false-positive suppression;
- stale versus in-flight distinction;
- anomalous divergence detection;
- deterministic Merkle-root evidence bundles;
- read-only RPC allowlist.
- config-driven Fuji live read path for ERC-20 lock/supply state.

Live Fuji reference deployment selection, Teleporter pending-message extraction, and hosted monitoring are intentionally not represented as complete yet.
