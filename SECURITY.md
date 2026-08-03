# Security Policy

## Scope

This project is a read-only observability tool. It does not require wallets, private keys, transaction signing, or custody of funds.

Security reports are in scope when they affect:

- read-only boundary enforcement;
- incorrect `anomalous`, `reconciled`, or `unverifiable` classification;
- evidence bundle integrity or Merkle determinism;
- API behavior that can misrepresent monitored state;
- documentation that could cause unsafe deployment assumptions.

Out of scope:

- Avalanche, Teleporter, ICTT, or third-party contract vulnerabilities not introduced by this tool;
- loss events caused by acting on an observatory signal without manual verification;
- denial-of-service against a user-supplied RPC provider.

## Reporting

Open a private security advisory on GitHub or contact the maintainer listed in `CITATION.cff`. Include reproduction steps, fixture/config inputs, observed output, expected output, and whether the issue requires live RPC access.

## Boundary

An `anomalous` classification is an investigation signal, not a vulnerability confirmation, audit opinion, or bounty submission.
