from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse

from .chain_client import JsonRpcClient, ReadOnlyRpcError
from .config import ObservatoryConfig, load_config

ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@dataclass(frozen=True)
class ReadinessCheck:
    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class ReadinessReport:
    ready: bool
    checks: tuple[ReadinessCheck, ...]


def valid_address(address: str) -> bool:
    return bool(ADDRESS_RE.fullmatch(address)) and address.lower() != ZERO_ADDRESS


def valid_public_url(url: str | None) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    return parsed.scheme == "https" and bool(parsed.netloc)


def check_config(config_path: Path | None) -> list[ReadinessCheck]:
    if config_path is None:
        return [
            ReadinessCheck(
                "live_config_present",
                "fail",
                "no live ICTT config supplied; fixture demo is not live deployment evidence",
            )
        ]
    if not config_path.exists():
        return [ReadinessCheck("live_config_present", "fail", f"config not found: {config_path}")]
    config = load_config(config_path)
    checks = [ReadinessCheck("live_config_present", "pass", str(config_path))]
    checks.extend(validate_config(config))
    return checks


def validate_config(config: ObservatoryConfig) -> list[ReadinessCheck]:
    checks: list[ReadinessCheck] = []
    if config.network != "fuji":
        checks.append(ReadinessCheck("network_is_fuji", "fail", f"network is {config.network!r}"))
    else:
        checks.append(ReadinessCheck("network_is_fuji", "pass", "Fuji testnet selected"))

    for chain in config.chains.values():
        if "REPLACE" in chain.rpc_url or not chain.rpc_url.startswith(("https://", "http://")):
            checks.append(ReadinessCheck("rpc_urls_configured", "fail", f"{chain.chain_id} has placeholder RPC URL"))
        else:
            checks.append(ReadinessCheck("rpc_urls_configured", "pass", f"{chain.chain_id} RPC URL configured"))

    if not config.deployments:
        return checks + [ReadinessCheck("deployments_configured", "fail", "no ICTT deployments configured")]

    checks.append(ReadinessCheck("deployments_configured", "pass", f"{len(config.deployments)} deployment(s) configured"))
    for deployment in config.deployments:
        addresses = {
            f"{deployment.deployment_id}.home.collateral_token": deployment.home.collateral_token,
            f"{deployment.deployment_id}.home.lock_contract": deployment.home.lock_contract,
            **{
                f"{deployment.deployment_id}.remote.{remote.chain_id}.token_contract": remote.token_contract
                for remote in deployment.remotes
            },
        }
        invalid = [name for name, address in addresses.items() if not valid_address(address)]
        if invalid:
            checks.append(
                ReadinessCheck(
                    "contract_addresses_configured",
                    "fail",
                    "placeholder or invalid address: " + ", ".join(sorted(invalid)),
                )
            )
        else:
            checks.append(
                ReadinessCheck(
                    "contract_addresses_configured",
                    "pass",
                    f"{deployment.deployment_id} has non-placeholder contract addresses",
                )
            )
    return checks


def configured_contract_addresses(config: ObservatoryConfig) -> list[tuple[str, str, str]]:
    addresses: list[tuple[str, str, str]] = []
    for deployment in config.deployments:
        addresses.append(
            (
                deployment.home.chain_id,
                f"{deployment.deployment_id}.home.collateral_token",
                deployment.home.collateral_token,
            )
        )
        addresses.append(
            (
                deployment.home.chain_id,
                f"{deployment.deployment_id}.home.lock_contract",
                deployment.home.lock_contract,
            )
        )
        addresses.extend(
            (
                remote.chain_id,
                f"{deployment.deployment_id}.remote.{remote.chain_id}.token_contract",
                remote.token_contract,
            )
            for remote in deployment.remotes
        )
    return addresses


def verify_contract_code(config: ObservatoryConfig) -> list[ReadinessCheck]:
    if not config.deployments:
        return [ReadinessCheck("live_contract_code", "fail", "no deployments to verify")]

    clients = {chain_id: JsonRpcClient(chain.rpc_url) for chain_id, chain in config.chains.items()}
    failures: list[str] = []
    verified = 0
    for chain_id, name, address in configured_contract_addresses(config):
        if not valid_address(address):
            failures.append(f"{name}: invalid address")
            continue
        client = clients.get(chain_id)
        if client is None:
            failures.append(f"{name}: missing chain config {chain_id}")
            continue
        try:
            code = client.call("eth_getCode", [address, "latest"])
        except ReadOnlyRpcError as exc:
            failures.append(f"{name}: RPC error {exc}")
            continue
        if not code or code == "0x":
            failures.append(f"{name}: no contract code at address")
        else:
            verified += 1

    if failures:
        return [ReadinessCheck("live_contract_code", "fail", "; ".join(failures))]
    return [ReadinessCheck("live_contract_code", "pass", f"{verified} contract address(es) have bytecode")]


def check_demo_data(demo_data: Path) -> list[ReadinessCheck]:
    required = ["bundle.json", "conservation.json", "correlation.json", "EXCEPTIONS.md", "merkle.json", "manifest.json"]
    missing = [name for name in required if not (demo_data / name).exists()]
    if missing:
        return [ReadinessCheck("demo_evidence_exported", "fail", "missing: " + ", ".join(missing))]

    conservation = json.loads((demo_data / "conservation.json").read_text(encoding="utf-8"))
    manifest = json.loads((demo_data / "manifest.json").read_text(encoding="utf-8"))
    merkle = json.loads((demo_data / "merkle.json").read_text(encoding="utf-8"))
    checks = [ReadinessCheck("demo_evidence_exported", "pass", str(demo_data))]

    if conservation.get("classification") == "anomalous" and conservation.get("unexplained_gap", 0) > 0:
        checks.append(ReadinessCheck("demo_shows_divergence", "pass", "anomalous divergence is visible"))
    else:
        checks.append(ReadinessCheck("demo_shows_divergence", "fail", "demo does not show an anomalous divergence"))

    if manifest.get("merkle_root") == merkle.get("root"):
        checks.append(ReadinessCheck("demo_merkle_matches_manifest", "pass", merkle["root"]))
    else:
        checks.append(ReadinessCheck("demo_merkle_matches_manifest", "fail", "manifest root differs from merkle.json"))
    return checks


def build_readiness_report(
    config_path: Path | None,
    demo_data: Path,
    public_demo_url: str | None,
    live_verify: bool = False,
) -> ReadinessReport:
    config = load_config(config_path) if config_path is not None and config_path.exists() else None
    checks = [
        *check_config(config_path),
        *(verify_contract_code(config) if live_verify and config is not None else []),
        *check_demo_data(demo_data),
        ReadinessCheck(
            "public_demo_url",
            "pass" if valid_public_url(public_demo_url) else "fail",
            public_demo_url or "no public HTTPS demo URL supplied",
        ),
    ]
    return ReadinessReport(
        ready=all(check.status == "pass" for check in checks),
        checks=tuple(checks),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether the repo is ready for a public live Fuji demo.")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--demo-data", type=Path, default=Path("web/demo-data"))
    parser.add_argument("--public-demo-url")
    parser.add_argument("--live-verify", action="store_true", help="Verify configured contract addresses have bytecode")
    args = parser.parse_args()

    report = build_readiness_report(args.config, args.demo_data, args.public_demo_url, live_verify=args.live_verify)
    print(json.dumps(asdict(report), indent=2, sort_keys=True))
    return 0 if report.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
