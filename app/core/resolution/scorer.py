from rapidfuzz.fuzz import ratio

from app.models.domain import Candidate, ProfileRecord
from .normalization import normalize_text, normalize_username

WEIGHTS = {
    "name": 0.24,
    "username": 0.20,
    "organization": 0.20,
    "location": 0.10,
    "bio": 0.14,
    "cross_links": 0.12,
}


def similarity(a: str | None, b: str | None) -> float:
    a_n, b_n = normalize_text(a), normalize_text(b)
    if not a_n or not b_n:
        return 0.0
    return ratio(a_n, b_n) / 100.0


def best_profile_match(query: ProfileRecord, profiles: list[ProfileRecord]) -> dict[str, float]:
    if not profiles:
        return {k: 0.0 for k in WEIGHTS}

    best = {k: 0.0 for k in WEIGHTS}
    for profile in profiles:
        best["name"] = max(best["name"], similarity(query.display_name, profile.display_name))
        best["username"] = max(
            best["username"],
            similarity(normalize_username(query.username), normalize_username(profile.username)),
        )
        best["organization"] = max(best["organization"], similarity(query.organization, profile.organization))
        best["location"] = max(best["location"], similarity(query.location, profile.location))
        best["bio"] = max(best["bio"], similarity(query.bio, profile.bio))

    # Cross-links are deliberately conservative: they are evidence that two records
    # explicitly point to each other, not a free-form semantic guess.
    urls = {str(p.url).lower() for p in profiles if p.url}
    query_meta = {str(v).lower() for v in query.metadata.values() if isinstance(v, str)}
    best["cross_links"] = 1.0 if urls & query_meta else 0.0
    return best


def resolve_candidate(query: ProfileRecord, candidate: Candidate):
    signals = best_profile_match(query, candidate.profiles)
    score = sum(signals[k] * WEIGHTS[k] for k in WEIGHTS) * 100
    return score, signals
