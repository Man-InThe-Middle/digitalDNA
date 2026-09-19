from __future__ import annotations

from collections import defaultdict
from app.models.domain import Evidence, ProfileRecord


def detect_claim_conflicts(evidence: list[Evidence]) -> list[str]:
    """Detect contradictory normalized values for the same signal type."""
    values: dict[str, set[str]] = defaultdict(set)
    for item in evidence:
        if item.signal_type in {"organization", "location", "name", "username"} and item.excerpt:
            values[item.signal_type].add(item.excerpt.strip().casefold())

    conflicts: list[str] = []
    for signal, observed in values.items():
        if len(observed) > 1:
            conflicts.append(f"Conflicting {signal} values observed: {sorted(observed)}")
    return conflicts


def detect_conflicts(profiles: list[ProfileRecord]) -> list[str]:
    """Detect contradictions directly from discovered profile records."""
    values: dict[str, set[str]] = defaultdict(set)
    for profile in profiles:
        for signal, value in (("name", profile.display_name), ("username", profile.username),
                              ("organization", profile.organization), ("location", profile.location)):
            if value:
                values[signal].add(value.strip().casefold())

    conflicts: list[str] = []
    for signal, observed in values.items():
        if len(observed) > 1:
            conflicts.append(f"Conflicting {signal} values observed: {sorted(observed)}")
    return conflicts
