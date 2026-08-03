# Prior Art

| Existing tool | What it does | What it does not do |
|---|---|---|
| `icm-services` relayer metrics | Relayer liveness, delivery counts, signature aggregation health | Economic consistency of the bridge |
| Snowtrace and explorers | Per-transaction and per-contract state inspection | Cross-chain aggregation and conservation math |
| ICTT contract events | Per-chain `TokensSent` and withdrawal history | Joined home-send to remote-receipt conservation state |
| Generic bridge monitors | Aggregate TVL or value display | Invariant verification with in-flight, fallback, and multi-hop classification |
| `avalanche-starter-kit` BuilderKit | Build-side ICTT and swap components | Independent observability or verification layer |

The unfilled gap is the cross-chain join: relayer telemetry answers whether messaging is up, and explorers answer what happened in one transaction. Neither answers whether total minted supply across remotes still equals locked collateral at home, nor whether a gap is explained by pending messages.
