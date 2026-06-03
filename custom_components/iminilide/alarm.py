from __future__ import annotations


def is_alarm_triggered(
    value: float,
    lower_threshold: float | None,
    upper_threshold: float | None,
) -> bool:
    """Return whether the current value is outside the configured alarm thresholds."""

    if lower_threshold is not None and upper_threshold is not None:
        return value < lower_threshold or value > upper_threshold
    if lower_threshold is not None:
        return value < lower_threshold
    if upper_threshold is not None:
        return value > upper_threshold
    return False
