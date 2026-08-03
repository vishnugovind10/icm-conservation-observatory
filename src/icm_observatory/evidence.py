from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .conservation import evaluate_conservation
from .models import DeploymentSnapshot


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def merkle_root(documents: dict[str, Any]) -> dict[str, Any]:
    leaves = {name: digest(payload) for name, payload in sorted(documents.items())}
    level = list(leaves.values())
    if not level:
        return {"root": hashlib.sha256(b"").hexdigest(), "leaves": leaves}
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])
        level = [
            hashlib.sha256((level[index] + level[index + 1]).encode("ascii")).hexdigest()
            for index in range(0, len(level), 2)
        ]
    return {"root": level[0], "leaves": leaves}


def build_evidence_bundle(
    snapshot: DeploymentSnapshot,
    stale_threshold_seconds: int,
    generated_at: str | None = None,
) -> dict[str, Any]:
    timestamp = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    result = evaluate_conservation(snapshot, stale_threshold_seconds)
    manifest = {
        "schema": "icm-conservation-evidence/v1",
        "tool_version": "0.1.0",
        "generated_at": timestamp,
        "deployment_id": snapshot.deployment_id,
        "chains": [asdict(snapshot.home_chain), *[asdict(chain) for chain in snapshot.remote_chains]],
        "stale_threshold_seconds": stale_threshold_seconds,
    }
    conservation = asdict(result)
    correlation = {
        "observation_summary": observation_summary(snapshot),
        "pending_messages": [asdict(message) for message in snapshot.pending_messages],
        "fallback_holdings": [asdict(holding) for holding in snapshot.fallback_holdings],
        "multi_hop_states": [asdict(state) for state in snapshot.multi_hop_states],
    }
    exceptions = render_exceptions(snapshot)
    commitment_manifest = {
        key: value for key, value in manifest.items() if key != "generated_at"
    }
    documents = {
        "bundle.json": commitment_manifest,
        "conservation.json": conservation,
        "correlation.json": correlation,
        "EXCEPTIONS.md": exceptions,
    }
    return {
        "bundle.json": manifest,
        "conservation.json": conservation,
        "correlation.json": correlation,
        "EXCEPTIONS.md": exceptions,
        "merkle.json": merkle_root(documents),
    }


def observation_summary(snapshot: DeploymentSnapshot) -> dict[str, Any]:
    return {
        "source": snapshot.metadata.get("observations_source", "none"),
        "note": snapshot.metadata.get("observations_note", ""),
        "pending_message_count": len(snapshot.pending_messages),
        "fallback_holding_count": len(snapshot.fallback_holdings),
        "multi_hop_state_count": len(snapshot.multi_hop_states),
    }


def render_exceptions(snapshot: DeploymentSnapshot) -> str:
    lines = [
        "# Exceptions",
        "",
    ]
    if snapshot.rpc_healthy:
        lines.append("No verification exceptions were recorded for this snapshot.")
    else:
        lines.extend(
            [
                "- Source: RPC",
                "- Reason: one or more required RPC sources is degraded",
                "- Effect: conservation state is unverifiable, not anomalous",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def write_evidence_bundle(bundle: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in bundle.items():
        target = output_dir / name
        if isinstance(payload, str):
            target.write_text(payload, encoding="utf-8")
        else:
            target.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
