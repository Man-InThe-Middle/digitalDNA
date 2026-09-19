from __future__ import annotations

import re
from collections import defaultdict
from typing import Iterable

from app.models.domain import Candidate, Evidence, ProfileRecord, SourceType

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)


def _source_reliability(source_type: SourceType) -> float:
    return {
        SourceType.PROFESSIONAL: 0.95,
        SourceType.CODE: 0.90,
        SourceType.WEBSITE: 0.85,
        SourceType.PUBLICATION: 0.90,
        SourceType.EVENT: 0.80,
        SourceType.SOCIAL: 0.65,
        SourceType.SEARCH: 0.45,
        SourceType.OTHER: 0.50,
    }[source_type]


def _add(evidence: list[Evidence], profile: ProfileRecord, claim: str, signal: str, excerpt: str | None = None) -> None:
    evidence.append(Evidence(
        source_url=profile.url,
        source_type=profile.source_type,
        claim=claim,
        excerpt=excerpt,
        signal_type=signal,
        reliability=_source_reliability(profile.source_type),
    ))


def extract_from_profiles(profiles: Iterable[ProfileRecord]) -> tuple[list[Candidate], list[Evidence]]:
    """Turn discovered profiles into candidates plus source-backed evidence.

    This layer deliberately does not decide identity. It only extracts claims and groups
    profiles by stable handles such as username/platform. Resolution remains downstream.
    """
    candidates_by_key: dict[str, Candidate] = {}
    evidence: list[Evidence] = []

    for profile in profiles:
        name = (profile.display_name or profile.username or "Unknown person").strip()
        key = (profile.username or profile.display_name or profile.url or profile.id).__str__().lower()
        candidate = candidates_by_key.setdefault(key, Candidate(name=name))
        candidate.profiles.append(profile)

        if profile.display_name:
            _add(evidence, profile, f"Profile display name is {profile.display_name}.", "name", profile.display_name)
        if profile.username:
            _add(evidence, profile, f"Public username is {profile.username}.", "username", profile.username)
        if profile.organization:
            _add(evidence, profile, f"Profile lists organization {profile.organization}.", "organization", profile.organization)
        if profile.location:
            _add(evidence, profile, f"Profile lists location {profile.location}.", "location", profile.location)
        if profile.bio:
            _add(evidence, profile, "Profile contains a public biography.", "bio", profile.bio[:500])

        for email in EMAIL_RE.findall(profile.bio or ""):
            _add(evidence, profile, f"Public profile exposes contact address {email}.", "contact", email)

    for candidate in candidates_by_key.values():
        candidate.evidence = [e for e in evidence if e.claim and any(p.url == e.source_url for p in candidate.profiles)]

    return list(candidates_by_key.values()), evidence
