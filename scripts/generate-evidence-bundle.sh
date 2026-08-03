#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-}:src"
python -m icm_observatory.cli --fixture "${1:-tests/fixtures/anomalous.json}" --evidence-dir "${2:-artifacts/evidence}"
python scripts/export_static_demo.py
