from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI

from icm_observatory.config import load_config
from icm_observatory.conservation import evaluate_conservation
from icm_observatory.evidence import build_evidence_bundle
from icm_observatory.fixtures import load_snapshot
from icm_observatory.live_snapshot import build_live_snapshot

app = FastAPI(title="ICM Conservation Observatory", version="0.1.0")
FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "anomalous.json"
DEFAULT_STALE_THRESHOLD_SECONDS = 180


def current_snapshot():
    config_path = os.environ.get("ICM_OBSERVATORY_CONFIG")
    if not config_path:
        return load_snapshot(FIXTURE), DEFAULT_STALE_THRESHOLD_SECONDS
    config = load_config(Path(config_path))
    if not config.deployments:
        raise RuntimeError("ICM_OBSERVATORY_CONFIG contains no deployments")
    deployment_id = os.environ.get("ICM_OBSERVATORY_DEPLOYMENT_ID")
    deployment = next(
        (item for item in config.deployments if deployment_id is None or item.deployment_id == deployment_id),
        None,
    )
    if deployment is None:
        raise RuntimeError(f"deployment not found in config: {deployment_id}")
    return build_live_snapshot(config, deployment), deployment.stale_threshold_seconds


@app.get("/conservation")
def conservation() -> dict:
    snapshot, stale_threshold = current_snapshot()
    return evaluate_conservation(snapshot, stale_threshold_seconds=stale_threshold).__dict__


@app.get("/classification")
def classification() -> dict:
    result = conservation()
    return {
        "deployment_id": result["deployment_id"],
        "classification": result["classification"],
        "alert_level": result["alert_level"],
        "reason": result["reason"],
    }


@app.get("/evidence")
def evidence() -> dict:
    snapshot, stale_threshold = current_snapshot()
    return build_evidence_bundle(snapshot, stale_threshold_seconds=stale_threshold, generated_at="2026-08-03T00:00:00+00:00")


@app.get("/metrics")
def metrics() -> str:
    result = conservation()
    return "\n".join(
        [
            f'icm_conservation_gap{{deployment_id="{result["deployment_id"]}"}} {result["unexplained_gap"]}',
            f'icm_conservation_alert{{classification="{result["classification"]}"}} 1',
            "",
        ]
    )
