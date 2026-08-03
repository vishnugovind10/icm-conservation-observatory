from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_powershell_readiness_wrapper_propagates_exit_code():
    script = (PROJECT_ROOT / "scripts" / "check-live-readiness.ps1").read_text(encoding="utf-8")
    assert "exit $LASTEXITCODE" in script
    assert "LiveVerify" in script


def test_static_packager_marks_fixture_demo_not_live_ready():
    script = (PROJECT_ROOT / "scripts" / "package_static_demo.py").read_text(encoding="utf-8")
    assert "ready_for_public_live_demo" in script
    assert "live Fuji ICTT config" in script
    assert "--config" in script
    assert "--observations" in script
