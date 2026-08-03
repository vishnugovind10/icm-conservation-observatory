param(
    [string]$Fixture = "tests/fixtures/anomalous.json",
    [string]$EvidenceDir = "artifacts/evidence"
)
$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "src;$env:PYTHONPATH"
python -m icm_observatory.cli --fixture $Fixture --evidence-dir $EvidenceDir
python scripts/export_static_demo.py
