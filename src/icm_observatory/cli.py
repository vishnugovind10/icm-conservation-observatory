from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config
from .conservation import evaluate_conservation
from .evidence import build_evidence_bundle, write_evidence_bundle
from .fixtures import load_snapshot
from .live_snapshot import build_live_snapshot
from .observations import ObservationValidationError, apply_observations_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate an ICTT conservation snapshot.")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--fixture", type=Path, default=Path("tests/fixtures/anomalous.json"))
    source.add_argument("--config", type=Path, help="JSON config for live read-only RPC monitoring")
    parser.add_argument("--deployment-id", help="deployment id from --config; defaults to the first deployment")
    parser.add_argument("--observations", type=Path, help="supplemental pending/fallback/multi-hop observations JSON")
    parser.add_argument("--stale-threshold-seconds", type=int, default=180)
    parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args()

    stale_threshold = args.stale_threshold_seconds
    if args.config:
        config = load_config(args.config)
        deployment = next(
            (
                item
                for item in config.deployments
                if args.deployment_id is None or item.deployment_id == args.deployment_id
            ),
            None,
        )
        if deployment is None:
            raise SystemExit(f"deployment not found in config: {args.deployment_id}")
        snapshot = build_live_snapshot(config, deployment)
        stale_threshold = deployment.stale_threshold_seconds
    else:
        snapshot = load_snapshot(args.fixture)
    try:
        snapshot = apply_observations_file(snapshot, args.observations)
    except ObservationValidationError as exc:
        raise SystemExit(f"invalid observations: {exc}") from exc

    result = evaluate_conservation(snapshot, stale_threshold)
    print(json.dumps(result.__dict__, indent=2, sort_keys=True, default=str))

    if args.evidence_dir:
        bundle = build_evidence_bundle(snapshot, stale_threshold)
        write_evidence_bundle(bundle, args.evidence_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
