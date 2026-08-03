from pathlib import Path

from icm_observatory.conservation import evaluate_conservation
from icm_observatory.fixtures import load_snapshot
from icm_observatory.models import Classification

FIXTURES = Path(__file__).parent / "fixtures"


def result_for(name: str):
    return evaluate_conservation(load_snapshot(FIXTURES / name), stale_threshold_seconds=180)


def test_reconciled_fixture_holds_invariant():
    result = result_for("reconciled.json")
    assert result.classification == Classification.RECONCILED
    assert result.raw_gap == 0
    assert result.unexplained_gap == 0


def test_in_flight_gap_is_not_alerted():
    result = result_for("in_flight.json")
    assert result.classification == Classification.IN_FLIGHT
    assert result.alert_level == "none"
    assert result.raw_gap == 0


def test_stale_pending_message_warns():
    result = result_for("stale.json")
    assert result.classification == Classification.STALE
    assert result.alert_level == "warning"
    assert result.unexplained_gap == 0


def test_anomalous_gap_is_critical():
    result = result_for("anomalous.json")
    assert result.classification == Classification.ANOMALOUS
    assert result.alert_level == "critical"
    assert result.unexplained_gap == 15000


def test_unverifiable_is_distinct_from_anomalous():
    result = result_for("unverifiable.json")
    assert result.classification == Classification.UNVERIFIABLE
    assert result.alert_level == "warning"
