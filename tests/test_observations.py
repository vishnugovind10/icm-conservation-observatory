import json
import os
import subprocess
import sys
from pathlib import Path

from icm_observatory.conservation import evaluate_conservation
from icm_observatory.fixtures import load_snapshot
from icm_observatory.models import Classification
from icm_observatory.observations import ObservationValidationError, apply_observations_file


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = PROJECT_ROOT / "tests" / "fixtures"


def test_observation_file_can_explain_fixture_gap_as_in_flight(tmp_path):
    observations = tmp_path / "observations.json"
    observations.write_text(
        json.dumps(
            {
                "source": "test-observation",
                "pending_messages": [
                    {
                        "message_id": "0xpending",
                        "source_chain": "fuji-c-chain",
                        "destination_chain": "fuji-l1-alpha",
                        "amount": 15000,
                        "age_seconds": 75,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    snapshot = apply_observations_file(load_snapshot(FIXTURES / "anomalous.json"), observations)
    result = evaluate_conservation(snapshot, stale_threshold_seconds=180)
    assert result.classification == Classification.IN_FLIGHT
    assert result.raw_gap == 0
    assert snapshot.metadata["observations_source"] == "test-observation"


def test_cli_accepts_observations_file(tmp_path):
    observations = tmp_path / "observations.json"
    observations.write_text(
        json.dumps(
            {
                "pending_messages": [
                    {
                        "message_id": "0xpending",
                        "source_chain": "fuji-c-chain",
                        "destination_chain": "fuji-l1-alpha",
                        "amount": 15000,
                        "age_seconds": 75,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    env = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "icm_observatory.cli",
            "--fixture",
            "tests/fixtures/anomalous.json",
            "--observations",
            str(observations),
        ],
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0
    assert '"classification": "in_flight"' in result.stdout


def test_packaged_observations_are_written_to_correlation(tmp_path, monkeypatch):
    import package_static_demo

    monkeypatch.setattr(package_static_demo, "PUBLIC_ROOT", tmp_path / "public")
    observations = tmp_path / "observations.json"
    observations.write_text(
        json.dumps(
            {
                "pending_messages": [
                    {
                        "message_id": "0xpending",
                        "source_chain": "fuji-c-chain",
                        "destination_chain": "fuji-l1-alpha",
                        "amount": 15000,
                        "age_seconds": 75,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    package_static_demo.package_demo(observations_path=observations)
    correlation = json.loads((tmp_path / "public" / "demo-data" / "correlation.json").read_text(encoding="utf-8"))
    conservation = json.loads((tmp_path / "public" / "demo-data" / "conservation.json").read_text(encoding="utf-8"))
    assert correlation["pending_messages"][0]["message_id"] == "0xpending"
    assert conservation["classification"] == "in_flight"


def test_observation_validation_rejects_unknown_chain_and_bad_amount(tmp_path):
    observations = tmp_path / "observations.json"
    observations.write_text(
        json.dumps(
            {
                "pending_messages": [
                    {
                        "message_id": "0xpending",
                        "source_chain": "unknown-chain",
                        "destination_chain": "fuji-l1-alpha",
                        "amount": 0,
                        "age_seconds": -1,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    try:
        apply_observations_file(load_snapshot(FIXTURES / "anomalous.json"), observations)
    except ObservationValidationError as exc:
        message = str(exc)
        assert "source_chain" in message
        assert "amount" in message
        assert "age_seconds" in message
    else:
        raise AssertionError("invalid observations were accepted")


def test_observation_validation_rejects_duplicate_pending_ids(tmp_path):
    observations = tmp_path / "observations.json"
    observations.write_text(
        json.dumps(
            {
                "pending_messages": [
                    {
                        "message_id": "0xpending",
                        "source_chain": "fuji-c-chain",
                        "destination_chain": "fuji-l1-alpha",
                        "amount": 1,
                        "age_seconds": 1,
                    },
                    {
                        "message_id": "0xpending",
                        "source_chain": "fuji-c-chain",
                        "destination_chain": "fuji-l1-alpha",
                        "amount": 1,
                        "age_seconds": 1,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    try:
        apply_observations_file(load_snapshot(FIXTURES / "anomalous.json"), observations)
    except ObservationValidationError as exc:
        assert "duplicates" in str(exc)
    else:
        raise AssertionError("duplicate observations were accepted")


def test_cli_rejects_invalid_observations_without_traceback(tmp_path):
    observations = tmp_path / "observations.json"
    observations.write_text(
        json.dumps(
            {
                "pending_messages": [
                    {
                        "message_id": "0xpending",
                        "source_chain": "fuji-c-chain",
                        "destination_chain": "fuji-l1-alpha",
                        "amount": -1,
                        "age_seconds": 1,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    env = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "icm_observatory.cli",
            "--fixture",
            "tests/fixtures/anomalous.json",
            "--observations",
            str(observations),
        ],
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert "invalid observations" in result.stderr
    assert "Traceback" not in result.stderr
