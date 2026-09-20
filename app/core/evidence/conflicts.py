from __future__ import annotations

from collections import defaultdict

from app.models.domain import ProfileRecord


def _norm(value: str | None) -> str:
    if not value:
        return ""

    return " ".join(
        value.casefold().strip().split()
    )


def _field_values(
    profiles: list[ProfileRecord],
    field: str,
) -> dict[str, list[ProfileRecord]]:

    grouped: dict[str, list[ProfileRecord]] = defaultdict(list)

    for profile in profiles:
        value = getattr(profile, field, None)

        if not value:
            continue

        normalized = _norm(str(value))

        if normalized:
            grouped[normalized].append(profile)

    return grouped


def _conflict_message(
    field: str,
    grouped: dict[str, list[ProfileRecord]],
) -> str:

    values = []

    for normalized, profiles in grouped.items():
        display_value = getattr(
            profiles[0],
            field,
            normalized,
        )

        platforms = ", ".join(
            sorted({
                p.platform
                for p in profiles
            })
        )

        values.append(
            f"{display_value} ({platforms})"
        )

    return (
        f"Conflicting public {field} values were "
        f"observed: {' vs '.join(values)}."
    )


def detect_conflicts(
    profiles: list[ProfileRecord],
) -> list[str]:

    conflicts: list[str] = []

    # --------------------------------------------------
    # ORGANIZATION
    # --------------------------------------------------

    organizations = _field_values(
        profiles,
        "organization",
    )

    if len(organizations) > 1:
        conflicts.append(
            _conflict_message(
                "organization",
                organizations,
            )
        )

    # --------------------------------------------------
    # LOCATION
    # --------------------------------------------------

    locations = _field_values(
        profiles,
        "location",
    )

    if len(locations) > 1:
        conflicts.append(
            _conflict_message(
                "location",
                locations,
            )
        )

    # --------------------------------------------------
    # DISPLAY NAME
    # --------------------------------------------------

    names = _field_values(
        profiles,
        "display_name",
    )

    if len(names) > 1:

        # Different display names are not automatically
        # identity conflicts because aliases / branding
        # can legitimately exist.
        conflicts.append(
            _conflict_message(
                "display_name",
                names,
            )
        )

    # --------------------------------------------------
    # PLATFORM USERNAMES
    # --------------------------------------------------

    usernames = _field_values(
        profiles,
        "username",
    )

    if len(usernames) >= 3:

        # Only surface this when there are substantially
        # different handles across several sources.
        conflicts.append(
            _conflict_message(
                "username",
                usernames,
            )
        )

    # --------------------------------------------------
    # TEMPORAL INTERPRETATION
    # --------------------------------------------------

    # Multiple organizations or locations can represent
    # legitimate movement over time. We deliberately
    # describe them as conflicts/potential conflicts,
    # rather than asserting that the identity is false.

    return conflicts