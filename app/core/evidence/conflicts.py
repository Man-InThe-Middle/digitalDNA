def detect_conflicts(profiles) -> list[str]:
    conflicts: list[str] = []
    orgs = {p.organization.strip().lower() for p in profiles if p.organization}
    locations = {p.location.strip().lower() for p in profiles if p.location}
    if len(orgs) > 1:
        conflicts.append("Multiple organizations are associated with this candidate.")
    if len(locations) > 1:
        conflicts.append("Multiple locations are associated with this candidate; this may be temporal rather than contradictory.")
    return conflicts
