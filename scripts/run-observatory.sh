#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-}:src"
if [[ -n "${ICM_OBSERVATORY_CONFIG:-}" ]]; then
  python -m icm_observatory.cli --config "$ICM_OBSERVATORY_CONFIG" --evidence-dir artifacts/evidence
else
  python -m icm_observatory.cli --fixture tests/fixtures/anomalous.json --evidence-dir artifacts/evidence
fi
