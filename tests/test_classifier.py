from pathlib import Path

from icm_observatory.conservation import evaluate_conservation
from icm_observatory.fixtures import load_snapshot
from icm_observatory.models import Classification

FIXTURES = Path(__file__).parent / "fixtures"


def test_fallback_holding_suppresses_false_anomaly():
    snapshot = load_snapshot(FIXTURES / "fallback.json")
    result = evaluate_conservation(snapshot, stale_threshold_seconds=180)
    assert result.classification == Classification.FALLBACK_HELD
    assert result.alert_level == "info"
    assert result.unexplained_gap == 0


def test_multi_hop_state_suppresses_false_anomaly():
    snapshot = load_snapshot(FIXTURES / "multi_hop.json")
    result = evaluate_conservation(snapshot, stale_threshold_seconds=180)
    assert result.classification == Classification.MULTI_HOP
    assert result.alert_level == "info"
    assert result.unexplained_gap == 0
