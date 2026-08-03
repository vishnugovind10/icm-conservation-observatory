# Limitations

- Current checked demo data is deterministic fixture evidence, not live Fuji ICTT state.
- A public HTTPS demo URL and real Fuji ICTT home/remote contract configuration are still required before presenting the dashboard as live evidence.
- `anomalous` is a signal for investigation, not proof of an exploit or confirmed vulnerability.
- RPC failures classify as `unverifiable`; deeper provider scoring remains future work.
- Relay baselines are observed, not protocol-specified.
- Multi-hop and fallback handling cover modeled cases only; novel ICTT integration patterns may require new classification logic.
- Mainnet monitoring is not enabled by default and must use user-supplied RPC configuration.
