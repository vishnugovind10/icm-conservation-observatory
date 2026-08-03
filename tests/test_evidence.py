from pathlib import Path

from icm_observatory.evidence import build_evidence_bundle, digest
from icm_observatory.fixtures import load_snapshot
from icm_observatory.observations import apply_observations

FIXTURES = Path(__file__).parent / "fixtures"


def test_same_state_produces_same_merkle_root():
    snapshot = load_snapshot(FIXTURES / "anomalous.json")
    first = build_evidence_bundle(snapshot, stale_threshold_seconds=180, generated_at="2026-08-03T00:00:00+00:00")
    second = build_evidence_bundle(snapshot, stale_threshold_seconds=180, generated_at="2026-08-03T00:00:00+00:00")
    assert first["merkle.json"]["root"] == second["merkle.json"]["root"]
    assert "conservation.json" in first["merkle.json"]["leaves"]


def test_wall_clock_generation_time_does_not_change_merkle_root():
    snapshot = load_snapshot(FIXTURES / "anomalous.json")
    first = build_evidence_bundle(snapshot, stale_threshold_seconds=180, generated_at="2026-08-03T00:00:00+00:00")
    second = build_evidence_bundle(snapshot, stale_threshold_seconds=180, generated_at="2026-08-03T00:01:00+00:00")
    assert first["bundle.json"]["generated_at"] != second["bundle.json"]["generated_at"]
    assert first["merkle.json"]["root"] == second["merkle.json"]["root"]
    assert first["merkle.json"]["leaves"]["bundle.json"] == second["merkle.json"]["leaves"]["bundle.json"]


def test_bundle_leaf_commits_to_manifest_without_generated_at():
    snapshot = load_snapshot(FIXTURES / "anomalous.json")
    bundle = build_evidence_bundle(snapshot, stale_threshold_seconds=180, generated_at="2026-08-03T00:00:00+00:00")
    committed_manifest = {key: value for key, value in bundle["bundle.json"].items() if key != "generated_at"}
    assert bundle["merkle.json"]["leaves"]["bundle.json"] == digest(committed_manifest)


def test_evidence_records_rpc_exceptions():
    snapshot = load_snapshot(FIXTURES / "unverifiable.json")
    bundle = build_evidence_bundle(snapshot, stale_threshold_seconds=180, generated_at="2026-08-03T00:00:00+00:00")
    assert "Source: RPC" in bundle["EXCEPTIONS.md"]
    assert "unverifiable" in bundle["EXCEPTIONS.md"]


def test_evidence_bundle_uses_spec_exception_filename():
    snapshot = load_snapshot(FIXTURES / "anomalous.json")
    bundle = build_evidence_bundle(snapshot, stale_threshold_seconds=180, generated_at="2026-08-03T00:00:00+00:00")
    assert "EXCEPTIONS.md" in bundle
    assert "EXCEPTIONS.json" not in bundle


def test_evidence_records_observation_summary_when_absent():
    snapshot = load_snapshot(FIXTURES / "anomalous.json")
    bundle = build_evidence_bundle(snapshot, stale_threshold_seconds=180, generated_at="2026-08-03T00:00:00+00:00")
    summary = bundle["correlation.json"]["observation_summary"]
    assert summary["source"] == "none"
    assert summary["pending_message_count"] == 0
    assert summary["fallback_holding_count"] == 0
    assert summary["multi_hop_state_count"] == 0


def test_evidence_records_observation_summary_when_supplied():
    snapshot = load_snapshot(FIXTURES / "anomalous.json")
    snapshot = apply_observations(
        snapshot,
        {
            "source": "test-observation-source",
            "note": "derived from test event correlation",
            "pending_messages": [
                {
                    "message_id": "0xpending",
                    "source_chain": "fuji-c-chain",
                    "destination_chain": "fuji-l1-alpha",
                    "amount": 15000,
                    "age_seconds": 75,
                }
            ],
        },
    )
    bundle = build_evidence_bundle(snapshot, stale_threshold_seconds=180, generated_at="2026-08-03T00:00:00+00:00")
    summary = bundle["correlation.json"]["observation_summary"]
    assert summary["source"] == "test-observation-source"
    assert summary["note"] == "derived from test event correlation"
    assert summary["pending_message_count"] == 1
    assert bundle["conservation.json"]["classification"] == "in_flight"
