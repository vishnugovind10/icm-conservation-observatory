from __future__ import annotations

import json
import shutil
import sys
from argparse import ArgumentParser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from icm_observatory.config import load_config
from icm_observatory.evidence import build_evidence_bundle, write_evidence_bundle
from icm_observatory.fixtures import load_snapshot
from icm_observatory.live_snapshot import build_live_snapshot
from icm_observatory.observations import apply_observations_file
from icm_observatory.readiness import build_readiness_report, valid_public_url

FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "anomalous.json"
WEB_ROOT = PROJECT_ROOT / "web"
PUBLIC_ROOT = PROJECT_ROOT / "public"


def copy_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def resolve_snapshot(config_path: Path | None, deployment_id: str | None, observations_path: Path | None):
    if config_path is None:
        snapshot = apply_observations_file(load_snapshot(FIXTURE), observations_path)
        return snapshot, 180, "deterministic divergence fixture", "fuji-fixture", "static-evidence-demo"

    config = load_config(config_path)
    deployment = next(
        (
            item
            for item in config.deployments
            if deployment_id is None or item.deployment_id == deployment_id
        ),
        None,
    )
    if deployment is None:
        raise SystemExit(f"deployment not found in config: {deployment_id}")
    snapshot = apply_observations_file(build_live_snapshot(config, deployment), observations_path)
    return snapshot, deployment.stale_threshold_seconds, f"live {config.network} RPC snapshot", config.network, "live-rpc-demo"


def package_demo(
    config_path: Path | None = None,
    deployment_id: str | None = None,
    public_demo_url: str | None = None,
    observations_path: Path | None = None,
) -> dict:
    if PUBLIC_ROOT.exists():
        shutil.rmtree(PUBLIC_ROOT)
    PUBLIC_ROOT.mkdir(parents=True)

    snapshot, stale_threshold, source, network, mode = resolve_snapshot(config_path, deployment_id, observations_path)
    bundle = build_evidence_bundle(
        snapshot,
        stale_threshold_seconds=stale_threshold,
        generated_at="2026-08-03T00:00:00+00:00",
    )
    write_evidence_bundle(bundle, WEB_ROOT / "demo-data")
    write_evidence_bundle(bundle, PUBLIC_ROOT / "demo-data")

    manifest = {
        "source": source,
        "files": sorted(bundle.keys()),
        "merkle_root": bundle["merkle.json"]["root"],
    }
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    (WEB_ROOT / "demo-data" / "manifest.json").write_text(manifest_text, encoding="utf-8")
    (PUBLIC_ROOT / "demo-data" / "manifest.json").write_text(manifest_text, encoding="utf-8")

    copy_file(WEB_ROOT / "index.html", PUBLIC_ROOT / "index.html")
    readiness = build_readiness_report(config_path, PUBLIC_ROOT / "demo-data", public_demo_url)
    readiness_checks = [
        {
            **check.__dict__,
            "detail": "demo-data" if check.name == "demo_evidence_exported" and check.status == "pass" else check.detail,
        }
        for check in readiness.checks
    ]
    ready_for_live_demo = readiness.ready and valid_public_url(public_demo_url)
    deployment_manifest = {
        "artifact": "icm-conservation-observatory-static-demo",
        "network": network,
        "mode": mode,
        "ready_for_public_live_demo": ready_for_live_demo,
        "reason": "Ready for public live demo." if ready_for_live_demo else "Public live demo still requires live Fuji ICTT config, anomalous demo evidence, and public HTTPS URL.",
        "entrypoint": "index.html",
        "evidence_root": bundle["merkle.json"]["root"],
        "public_demo_url": public_demo_url,
        "readiness": {
            "ready": readiness.ready,
            "checks": readiness_checks,
        },
    }
    (PUBLIC_ROOT / "deployment-manifest.json").write_text(
        json.dumps(deployment_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return deployment_manifest


def main() -> int:
    parser = ArgumentParser(description="Build a static demo package from fixture or live Fuji config.")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--deployment-id")
    parser.add_argument("--public-demo-url")
    parser.add_argument("--observations", type=Path)
    args = parser.parse_args()
    package_demo(args.config, args.deployment_id, args.public_demo_url, args.observations)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
