from __future__ import annotations

import re
from rapidfuzz import fuzz

from app.models.domain import Candidate, ProfileRecord


def _norm(value: str | None) -> str:
    if not value:
        return ""
    value = value.casefold().strip()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value


def _tokens(value: str | None) -> set[str]:
    return {
        token
        for token in _norm(value).split()
        if len(token) > 1
    }


def _name_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0

    direct = fuzz.token_set_ratio(a, b) / 100.0

    a_tokens = _tokens(a)
    b_tokens = _tokens(b)

    if a_tokens and b_tokens:
        overlap = len(a_tokens & b_tokens) / max(
            len(a_tokens | b_tokens),
            1,
        )
    else:
        overlap = 0.0

    return round(max(direct, overlap), 3)


def _username_similarity(subject: str, username: str | None) -> float:
    if not subject or not username:
        return 0.0

    subject_norm = _norm(subject).replace(" ", "")
    username_norm = _norm(username).replace(" ", "")

    if not subject_norm or not username_norm:
        return 0.0

    ratio = fuzz.ratio(subject_norm, username_norm) / 100.0

    subject_parts = subject_norm.split()
    first = subject_parts[0] if subject_parts else ""

    if first and first in username_norm:
        ratio = max(ratio, 0.65)

    return round(min(ratio, 1.0), 3)


def _text_similarity(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 0.0

    return round(
        fuzz.token_set_ratio(
            _norm(a),
            _norm(b),
        ) / 100.0,
        3,
    )


def _organization_overlap(
    profiles: list[ProfileRecord],
) -> float:
    organizations = {
        _norm(profile.organization)
        for profile in profiles
        if profile.organization
    }

    organizations.discard("")

    if len(organizations) == 1 and organizations:
        return 1.0

    if len(organizations) > 1:
        return 0.35

    return 0.0


def _location_overlap(
    profiles: list[ProfileRecord],
) -> float:
    locations = {
        _norm(profile.location)
        for profile in profiles
        if profile.location
    }

    locations.discard("")

    if len(locations) == 1 and locations:
        return 1.0

    if len(locations) > 1:
        return 0.25

    return 0.0


def score_candidate(
    subject_label: str,
    candidate: Candidate,
) -> tuple[float, dict[str, float], list[str]]:
    profiles = candidate.profiles

    if not profiles:
        return 0.0, {}, ["No public profiles were discovered."]

    names = [
        profile.display_name
        for profile in profiles
        if profile.display_name
    ]

    name_scores = [
        _name_similarity(subject_label, name)
        for name in names
    ]

    name_signal = max(name_scores, default=0.0)

    username_scores = [
        _username_similarity(
            subject_label,
            profile.username,
        )
        for profile in profiles
    ]

    username_signal = max(username_scores, default=0.0)

    organization_signal = _organization_overlap(profiles)
    location_signal = _location_overlap(profiles)

    bio_scores = [
        _text_similarity(
            subject_label,
            profile.bio,
        )
        for profile in profiles
        if profile.bio
    ]

    bio_signal = max(bio_scores, default=0.0)

    cross_source_signal = min(
        len(profiles) / 5.0,
        1.0,
    )

    signals = {
        "name_match": round(name_signal, 3),
        "username_match": round(username_signal, 3),
        "organization_overlap": round(organization_signal, 3),
        "location_overlap": round(location_signal, 3),
        "bio_match": round(bio_signal, 3),
        "cross_source_support": round(cross_source_signal, 3),
    }

    weights = {
        "name_match": 0.30,
        "username_match": 0.20,
        "organization_overlap": 0.15,
        "location_overlap": 0.10,
        "bio_match": 0.10,
        "cross_source_support": 0.15,
    }

    score = sum(
        signals[key] * weights[key]
        for key in signals
    )

    explanations: list[str] = []

    if name_signal >= 0.85:
        explanations.append(
            "Strong display-name similarity with the investigation subject."
        )
    elif name_signal >= 0.60:
        explanations.append(
            "Partial display-name similarity was found."
        )
    else:
        explanations.append(
            "Display-name similarity is weak."
        )

    if username_signal >= 0.80:
        explanations.append(
            "At least one public username strongly resembles the subject name."
        )
    elif username_signal >= 0.50:
        explanations.append(
            "A public username has partial similarity to the subject."
        )

    if organization_signal >= 0.90:
        explanations.append(
            "Multiple discovered profiles share the same organization."
        )
    elif organization_signal > 0:
        explanations.append(
            "Organization information is present but not fully consistent."
        )

    if location_signal >= 0.90:
        explanations.append(
            "Multiple profiles report the same location."
        )
    elif location_signal > 0:
        explanations.append(
            "Location information is inconsistent across sources."
        )

    if bio_signal >= 0.70:
        explanations.append(
            "Profile biography text contains meaningful subject overlap."
        )

    if len(profiles) >= 3:
        explanations.append(
            f"{len(profiles)} independent public profiles contribute to this candidate."
        )
    elif len(profiles) == 2:
        explanations.append(
            "Two public profiles contribute to this candidate."
        )
    else:
        explanations.append(
            "Only one public profile contributes to this candidate."
        )

    return round(score * 100, 2), signals, explanations