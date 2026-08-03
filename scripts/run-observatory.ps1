$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "src;$env:PYTHONPATH"
if ($env:ICM_OBSERVATORY_CONFIG) {
    python -m icm_observatory.cli --config $env:ICM_OBSERVATORY_CONFIG --evidence-dir artifacts/evidence
} else {
    python -m icm_observatory.cli --fixture tests/fixtures/anomalous.json --evidence-dir artifacts/evidence
}
