# Assumptions and Limits

## Measured

- Fixture tests measure the conservation equation and all classification labels.
- Evidence bundle determinism is measured by repeating the same state and comparing the Merkle root. `generated_at` is operator metadata and is intentionally excluded from the Merkle commitment so identical block state can reproduce the same root.
- The read-only boundary is measured by allowlisted RPC methods and tests that reject signing-related code paths.
- The live Fuji RPC smoke can verify C-Chain chain ID and block height when `ICM_LIVE_TESTS=1` is set.

## Estimated

- Relay stale thresholds are derived from observed relay timing. The default threshold in examples is a fixture value, not a calibrated Fuji network SLA.
- Fallback and multi-hop handling models the known structural cases in the build spec; novel integration patterns may need additional classification logic.
- Supplemental observations are accepted only as explicit JSON inputs, validated before classification, and written into `correlation.json`; they are not inferred silently.
- Evidence bundles include `observation_summary` so observation provenance and absence are committed in the Merkle root.

## Unknown

- A live RPC endpoint may return stale or incorrect data. The current implementation treats failed health checks and failed reads as `unverifiable`; deeper provider scoring is still a Phase 4 requirement.
- An `anomalous` result is an investigation signal, not a confirmed vulnerability or audit finding.
- Third-party ICTT deployments may be monitorable, but their scope, bounty relevance, and integration behavior must be verified independently.
