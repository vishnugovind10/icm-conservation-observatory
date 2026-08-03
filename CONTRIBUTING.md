# Contributing

Contributions should preserve the core constraints:

- no private keys, wallets, transaction signing, or write RPC calls;
- Fuji Testnet by default;
- live output must distinguish observed, inferred, and unverifiable state;
- fixture tests must remain network-free;
- live-readiness checks must fail closed when live config or public demo evidence is missing.

## Development

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python scripts/package_static_demo.py
.\scripts\check-live-readiness.ps1 -Config config/fuji.example.json
```

The example readiness command is expected to exit `1` until real Fuji ICTT deployment addresses and a public HTTPS demo URL are supplied.

## Pull Request Checklist

- Add or update tests for changed logic.
- Keep `tests/live/*` opt-in only.
- Update `BUILD_REPORT.md` when verification evidence changes.
- Do not add Ava Labs source code, vendored contracts, or copied implementation files.
- Do not claim live deployment readiness unless `check-live-readiness` passes with live Fuji config and a public URL.
