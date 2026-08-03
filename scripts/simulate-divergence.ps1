$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "src;$env:PYTHONPATH"
python -m icm_observatory.cli --fixture tests/fixtures/anomalous.json --evidence-dir artifacts/evidence
