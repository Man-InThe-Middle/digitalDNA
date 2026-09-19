from __future__ import annotations

from collections import defaultdict
from app.models.domain import Evidence, ProfileRecord


def detect_claim_conflicts(evidence: list[Evidence]) -> list[str]:
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
    """Detect contradictory identity claims while ignoring event-context records."""
    values: dict[str, set[str]] = defaultdict(set)
    for profile in profiles:
        # Event pages can describe a venue/host/context rather than employment or residence.
        if str(profile.source_type).lower().endswith("event") or getattr(profile.source_type, "value", None) == "event":
            continue
        for signal, value in (
            ("name", profile.display_name),
            ("username", profile.username),
            ("organization", profile.organization),
            ("location", profile.location),
        ):
            if value:
                values[signal].add(value.strip().casefold())

    conflicts: list[str] = []
    for signal, observed in values.items():
        if len(observed) > 1:
            conflicts.append(f"Conflicting {signal} values observed: {sorted(observed)}")
    return conflicts


def structured_conflicts(profiles: list[ProfileRecord]) -> list[dict]:
    """Return source-aware conflict objects for API/report consumers."""
    out: list[dict] = []
    fields = ("name", "username", "organization", "location")

    for field in fields:
        observations: dict[str, list[ProfileRecord]] = defaultdict(list)
        for profile in profiles:
            if getattr(profile.source_type, "value", str(profile.source_type)) == "event":
                continue
            value = getattr(profile, field, None)
            if value:
                observations[value.strip().casefold()].append(profile)

        if len(observations) > 1:
            out.append({
                "field": field,
                "values": [
                    {
                        "value": key,
                        "sources": [p.platform for p in records],
                        "profile_ids": [str(p.id) for p in records],
                    }
                    for key, records in observations.items()
                ],
                "interpretation": "Multiple public sources report different values; the system does not silently choose one.",
            })

    return out
