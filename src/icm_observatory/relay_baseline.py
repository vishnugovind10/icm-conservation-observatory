from __future__ import annotations

from statistics import median


def stale_threshold_seconds(observed_relay_seconds: list[int], multiplier: int = 3, floor_seconds: int = 60) -> int:
    if multiplier < 1:
        raise ValueError("multiplier must be positive")
    if not observed_relay_seconds:
        return floor_seconds
    return max(floor_seconds, int(median(observed_relay_seconds) * multiplier))
