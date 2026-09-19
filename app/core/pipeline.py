from __future__ import annotations

from rapidfuzz.fuzz import ratio

from app.config import settings
from app.core.demo import demo_profiles
from app.core.discovery.base import DiscoveryQuery
from app.core.discovery.github import GitHubDiscoveryProvider
from app.core.discovery.service import DiscoveryService
from app.core.discovery.web import DuckDuckGoWebDiscoveryProvider
from app.core.evidence.conflicts import detect_conflicts
from app.models.domain import (
    Candidate,
    Evidence,
    Investigation,
    ProfileRecord,
    ResolutionResult,
    ResolutionStatus,
)


def _norm(value: str | None) -> str:
    return "".join(
        ch.lower()
        for ch in (value or "")
        if ch.isalnum()
    )


def _sim(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 0.0

    a = _norm(a)
    b = _norm(b)

    if not a or not b:
        return 0.0

    return ratio(a, b) / 100.0


# ---------------------------------------------------------
# IDENTITY CLUSTERING
# ---------------------------------------------------------

def _cluster_profiles(
    profiles: list[ProfileRecord],
) -> list[Candidate]:

    candidates: list[Candidate] = []

    for profile in profiles:

        placed = False

        for candidate in candidates:

            anchor = candidate.profiles[0]

            name_similarity = _sim(
                profile.display_name,
                anchor.display_name
            )

            username_similarity = _sim(
                profile.username,
                anchor.username
            )

            organization_similarity = _sim(
                profile.organization,
                anchor.organization
            )

            same_url = bool(
                profile.url
                and anchor.url
                and str(profile.url).lower()
                == str(anchor.url).lower()
            )

            same_identity = (
                same_url
                or name_similarity >= 0.78
                or username_similarity >= 0.82
                or (
                    organization_similarity >= 0.90
                    and name_similarity >= 0.62
                )
            )

            if same_identity:

                candidate.profiles.append(profile)
                placed = True
                break

        if not placed:

            candidates.append(
                Candidate(
                    name=(
                        profile.display_name
                        or profile.username
                        or "Unknown"
                    ),
                    profiles=[profile]
                )
            )

    return candidates


# ---------------------------------------------------------
# MULTI-SIGNAL RESOLUTION
# ---------------------------------------------------------

def _signals(
    subject: str,
    context: str | None,
    candidate: Candidate,
) -> dict[str, float]:

    profiles = candidate.profiles

    names = [
        _sim(subject, p.display_name)
        for p in profiles
    ]

    organizations = [
        p.organization
        for p in profiles
        if p.organization
    ]

    locations = [
        p.location
        for p in profiles
        if p.location
    ]

    bios = [
        p.bio
        for p in profiles
        if p.bio
    ]

    usernames = [
        p.username
        for p in profiles
        if p.username
    ]

    # 1. Name
    name_similarity = max(
        names or [0.0]
    )

    # 2. Username consistency
    username_consistency = 0.0

    for i, a in enumerate(usernames):

        for b in usernames[i + 1:]:

            username_consistency = max(
                username_consistency,
                _sim(a, b)
            )

    # 3. Organization overlap
    organization_overlap = (
        1.0
        if organizations
        and len({_norm(x) for x in organizations}) == 1
        else 0.0
    )

    # 4. Location overlap
    location_overlap = (
        1.0
        if locations
        and len({_norm(x) for x in locations}) == 1
        else 0.0
    )

    # 5. Context / biography similarity
    bio_context_similarity = 0.0

    if context and bios:

        bio_context_similarity = max(
            _sim(context, bio)
            for bio in bios
        )

    elif bios:

        # Internal coherence signal only.
        bio_context_similarity = min(
            1.0,
            0.55 + (0.12 * len(bios))
        )

    # 6. Explicit cross-source links
    explicit_cross_links = 0.0

    urls = {
        str(p.url).lower()
        for p in profiles
        if p.url
    }

    for profile in profiles:

        for value in profile.metadata.values():

            if not isinstance(value, str):
                continue

            if not value.startswith(
                ("http://", "https://")
            ):
                continue

            if any(
                value.lower() in url
                or url in value.lower()
                for url in urls
            ):
                explicit_cross_links = 1.0

    # 7. Independent source diversity
    source_diversity = min(
        1.0,
        len({
            p.source_type.value
            for p in profiles
        }) / 4.0
    )

    return {
        "name_similarity":
            round(name_similarity, 4),

        "username_consistency":
            round(username_consistency, 4),

        "organization_overlap":
            round(organization_overlap, 4),

        "location_overlap":
            round(location_overlap, 4),

        "bio_context_similarity":
            round(bio_context_similarity, 4),

        "explicit_cross_links":
            round(explicit_cross_links, 4),

        "source_diversity":
            round(source_diversity, 4),
    }


def _score(
    signals: dict[str, float]
) -> float:

    weights = {

        "name_similarity": 0.28,

        "username_consistency": 0.14,

        "organization_overlap": 0.18,

        "location_overlap": 0.08,

        "bio_context_similarity": 0.10,

        "explicit_cross_links": 0.14,

        "source_diversity": 0.08,
    }

    score = sum(
        signals[key] * weights[key]
        for key in weights
    )

    return round(score * 100, 2)


# ---------------------------------------------------------
# EVIDENCE GENERATION
# ---------------------------------------------------------

def _evidence_for(
    candidate: Candidate,
    signals: dict[str, float],
) -> list[Evidence]:

    evidence: list[Evidence] = []

    for profile in candidate.profiles:

        if profile.display_name:

            evidence.append(
                Evidence(
                    source_url=profile.url,
                    source_type=profile.source_type,

                    claim=(
                        f"{profile.platform} publicly "
                        f"identifies the account as "
                        f"{profile.display_name}."
                    ),

                    excerpt=profile.display_name,

                    signal_type="name_similarity",

                    weight=signals[
                        "name_similarity"
                    ],

                    reliability=(
                        0.95
                        if profile.source_type.value
                        == "professional"
                        else 0.75
                    ),
                )
            )

        if profile.organization:

            evidence.append(
                Evidence(
                    source_url=profile.url,
                    source_type=profile.source_type,

                    claim=(
                        f"{profile.platform} associates "
                        f"the profile with "
                        f"{profile.organization}."
                    ),

                    excerpt=profile.organization,

                    signal_type="organization_overlap",

                    weight=signals[
                        "organization_overlap"
                    ],

                    reliability=0.90,
                )
            )

        if profile.location:

            evidence.append(
                Evidence(
                    source_url=profile.url,
                    source_type=profile.source_type,

                    claim=(
                        f"{profile.platform} publicly "
                        f"lists {profile.location}."
                    ),

                    excerpt=profile.location,

                    signal_type="location_overlap",

                    weight=signals[
                        "location_overlap"
                    ],

                    reliability=0.70,
                )
            )

        if profile.username:

            evidence.append(
                Evidence(
                    source_url=profile.url,
                    source_type=profile.source_type,

                    claim=(
                        f"Public account handle is "
                        f"@{profile.username}."
                    ),

                    excerpt=profile.username,

                    signal_type="username_consistency",

                    weight=signals[
                        "username_consistency"
                    ],

                    reliability=0.80,
                )
            )

        # Explicit links between public sources
        for value in profile.metadata.values():

            if (
                isinstance(value, str)
                and value.startswith(
                    ("http://", "https://")
                )
            ):

                evidence.append(
                    Evidence(
                        source_url=profile.url,
                        source_type=profile.source_type,

                        claim=(
                            f"{profile.platform} contains "
                            "an explicit public link to "
                            "another source."
                        ),

                        excerpt=value,

                        signal_type="explicit_cross_link",

                        weight=signals[
                            "explicit_cross_links"
                        ],

                        reliability=0.98,
                    )
                )

    return evidence


# ---------------------------------------------------------
# TIMELINE
# ---------------------------------------------------------

def _timeline(
    profiles: list[ProfileRecord],
) -> list[dict]:

    events = []

    for profile in profiles:

        metadata = profile.metadata or {}

        date = (
            metadata.get("event_date")
            or metadata.get("joined")
            or metadata.get("date")
        )

        if not date:
            continue

        title = (
            metadata.get("role")
            or metadata.get("event")
            or f"{profile.platform} activity"
        )

        events.append(
            {
                "date": str(date),

                "title": str(title),

                "source": profile.platform,

                "url": (
                    str(profile.url)
                    if profile.url
                    else None
                ),

                "type": "activity",
            }
        )

    return sorted(
        events,
        key=lambda x: x["date"]
    )


# ---------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------

async def run_pipeline(
    inv: Investigation,
):

    providers = []

    if settings.live_discovery:

        providers = [
            GitHubDiscoveryProvider(
                token=settings.github_token
            ),

            DuckDuckGoWebDiscoveryProvider(),
        ]

    discovered: list[ProfileRecord] = []

    if providers:

        service = DiscoveryService(
            providers
        )

        discovered = await service.discover(
            DiscoveryQuery(
                inv.subject_label
            )
        )

    # -----------------------------------------------------
    # DEMO FALLBACK
    # -----------------------------------------------------

    if not discovered:

        discovered = demo_profiles(
            inv.subject_label
        )

        discovery_mode = (
            "synthetic_demo_fallback"
        )

    else:

        discovery_mode = (
            "live_public_sources"
        )

    # -----------------------------------------------------
    # CLUSTER
    # -----------------------------------------------------

    candidates = _cluster_profiles(
        discovered
    )

    scored = []

    for candidate in candidates:

        signals = _signals(
            inv.subject_label,
            inv.context,
            candidate
        )

        score = _score(
            signals
        )

        evidence = _evidence_for(
            candidate,
            signals
        )

        candidate.evidence = evidence

        conflicts = detect_conflicts(
            candidate.profiles
        )

        scored.append(
            (
                score,
                candidate,
                signals,
                conflicts,
            )
        )

    scored.sort(
        key=lambda item: item[0],
        reverse=True
    )

    # -----------------------------------------------------
    # NOTHING FOUND
    # -----------------------------------------------------

    if not scored:

        candidate = Candidate(
            name=inv.subject_label
        )

        result = ResolutionResult(
            candidate_id=candidate.id,
            score=0,

            status=(
                ResolutionStatus
                .INSUFFICIENT_EVIDENCE
            ),

            signals={},
            conflicts=[],
        )

        return {
            "profiles": [],
            "candidate": candidate,
            "resolution": result,
            "timeline": [],
            "conflicts": [],
            "discovery_mode": discovery_mode,
        }

    # -----------------------------------------------------
    # BEST IDENTITY CLUSTER
    # -----------------------------------------------------

    score, candidate, signals, raw_conflicts = (
        scored[0]
    )

    if raw_conflicts and score >= 55:

        status = (
            ResolutionStatus.CONFLICT
        )

    elif score >= 85:

        status = (
            ResolutionStatus.VERIFIED
        )

    elif score >= 70:

        status = (
            ResolutionStatus.PROBABLE
        )

    elif score >= 50:

        status = (
            ResolutionStatus.POSSIBLE
        )

    else:

        status = (
            ResolutionStatus
            .INSUFFICIENT_EVIDENCE
        )

    result = ResolutionResult(

        candidate_id=candidate.id,

        score=score,

        status=status,

        signals=signals,

        supporting_evidence=[
            e.id
            for e in candidate.evidence
        ],

        conflicts=raw_conflicts,
    )

    timeline = _timeline(
        candidate.profiles
    )

    conflicts = []

    for conflict in raw_conflicts:

        conflicts.append(
            {
                "field":
                    "cross_source_claim",

                "values": [],

                "interpretation":
                    conflict,
            }
        )

    return {

        "profiles":
            candidate.profiles,

        "candidate":
            candidate,

        "resolution":
            result,

        "timeline":
            timeline,

        "conflicts":
            conflicts,

        "discovery_mode":
            discovery_mode,
    }