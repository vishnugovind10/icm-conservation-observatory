from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from icm_observatory.evidence import build_evidence_bundle, write_evidence_bundle
from icm_observatory.fixtures import load_snapshot


FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "anomalous.json"
OUTPUT = PROJECT_ROOT / "web" / "demo-data"


def main() -> int:
    snapshot = load_snapshot(FIXTURE)
    bundle = build_evidence_bundle(
        snapshot,
        stale_threshold_seconds=180,
        generated_at="2026-08-03T00:00:00+00:00",
    )
    write_evidence_bundle(bundle, OUTPUT)
    manifest = {
        "source": "deterministic divergence fixture",
        "files": sorted(bundle.keys()),
        "merkle_root": bundle["merkle.json"]["root"],
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
