from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_ci_workflow_runs_offline_tests_and_readiness_gate():
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "python -m pytest -q" in workflow
    assert "python scripts/package_static_demo.py" in workflow
    assert "./scripts/check-live-readiness.sh config/fuji.example.json" in workflow
    assert "ICM_LIVE_TESTS" in workflow
    assert "fail-fast: false" in workflow
    assert "check-live-readiness" in workflow


def test_pages_workflow_publishes_only_not_ready_fixture_package():
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
    assert "python scripts/package_static_demo.py" in workflow
    assert "ready_for_public_live_demo" in workflow
    assert "static-evidence-demo" in workflow
    assert "actions/deploy-pages" in workflow
    assert "path: public" in workflow


def test_public_release_hygiene_files_exist_and_preserve_boundaries():
    for name in ["SECURITY.md", "CONTRIBUTING.md", "LIMITATIONS.md", "CITATION.cff", "DEPLOYMENT.md"]:
        assert (PROJECT_ROOT / name).exists()

    security = (PROJECT_ROOT / "SECURITY.md").read_text(encoding="utf-8")
    limitations = (PROJECT_ROOT / "LIMITATIONS.md").read_text(encoding="utf-8")
    contributing = (PROJECT_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    citation = (PROJECT_ROOT / "CITATION.cff").read_text(encoding="utf-8")
    deployment = (PROJECT_ROOT / "DEPLOYMENT.md").read_text(encoding="utf-8")

    assert "read-only" in security
    assert "not a vulnerability confirmation" in security
    assert "not live Fuji ICTT state" in limitations
    assert "no private keys" in contributing
    assert "Apache-2.0" in citation
    assert "not live Fuji ICTT monitoring" in deployment
