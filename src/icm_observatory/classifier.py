from __future__ import annotations

from .models import Classification, DeploymentSnapshot


def classify_gap(
    snapshot: DeploymentSnapshot,
    raw_gap: int,
    stale_threshold_seconds: int,
) -> tuple[Classification, str, str, int]:
    if not snapshot.rpc_healthy:
        return (
            Classification.UNVERIFIABLE,
            "required RPC source is degraded; conservation state is unknown",
            "warning",
            abs(raw_gap),
        )

    if abs(raw_gap) <= snapshot.tolerance:
        stale_messages = [
            message for message in snapshot.pending_messages if message.age_seconds > stale_threshold_seconds
        ]
        if stale_messages:
            return (
                Classification.STALE,
                f"{len(stale_messages)} pending message(s) exceed the relay baseline threshold",
                "warning",
                0,
            )
        if snapshot.pending_messages:
            return (
                Classification.IN_FLIGHT,
                "gap is fully explained by pending Teleporter messages within the relay baseline",
                "none",
                0,
            )
        return (Classification.RECONCILED, "locked collateral equals minted supply", "none", 0)

    fallback_amount = sum(holding.amount for holding in snapshot.fallback_holdings)
    if abs(raw_gap - fallback_amount) <= snapshot.tolerance:
        return (
            Classification.FALLBACK_HELD,
            "gap is explained by sendAndCall fallback recipient holdings",
            "info",
            0,
        )

    multihop_amount = sum(state.amount for state in snapshot.multi_hop_states)
    if abs(raw_gap - multihop_amount) <= snapshot.tolerance:
        return (
            Classification.MULTI_HOP,
            "gap is explained by an intermediate multi-hop transfer state",
            "info",
            0,
        )

    return (
        Classification.ANOMALOUS,
        "gap is not explained by pending messages, fallback holdings, or multi-hop state",
        "critical",
        abs(raw_gap),
    )
