#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-}:src"
python -m icm_observatory.cli --fixture tests/fixtures/anomalous.json --evidence-dir artifacts/evidence
