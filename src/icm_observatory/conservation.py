from __future__ import annotations

from .classifier import classify_gap
from .models import ConservationResult, DeploymentSnapshot


def evaluate_conservation(snapshot: DeploymentSnapshot, stale_threshold_seconds: int) -> ConservationResult:
    total_minted = sum(snapshot.minted_supply.values())
    pending_amount = sum(message.amount for message in snapshot.pending_messages)
    raw_gap = snapshot.locked_collateral - total_minted - pending_amount
    classification, reason, alert_level, unexplained_gap = classify_gap(
        snapshot=snapshot,
        raw_gap=raw_gap,
        stale_threshold_seconds=stale_threshold_seconds,
    )
    return ConservationResult(
        deployment_id=snapshot.deployment_id,
        locked_collateral=snapshot.locked_collateral,
        total_minted_supply=total_minted,
        pending_amount=pending_amount,
        raw_gap=raw_gap,
        unexplained_gap=unexplained_gap,
        classification=classification,
        reason=reason,
        alert_level=alert_level,
    )
