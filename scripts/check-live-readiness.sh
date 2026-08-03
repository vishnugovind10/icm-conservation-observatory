#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-}:src"
CONFIG="${1:-config/fuji.example.json}"
PUBLIC_DEMO_URL="${2:-}"
LIVE_VERIFY="${3:-}"

ARGS=(--config "$CONFIG")
if [[ -n "$PUBLIC_DEMO_URL" ]]; then
  ARGS+=(--public-demo-url "$PUBLIC_DEMO_URL")
fi
if [[ "$LIVE_VERIFY" == "--live-verify" || "$LIVE_VERIFY" == "live" ]]; then
  ARGS+=(--live-verify)
fi
python -m icm_observatory.readiness "${ARGS[@]}"
