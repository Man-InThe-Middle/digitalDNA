from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from uuid import UUID, uuid4

from app.core.evidence.conflicts import detect_conflicts
from app.core.resolution.scorer import similarity
from app.models.domain import Candidate, ProfileRecord, ResolutionResult, ResolutionStatus


@dataclass
class IdentityCluster:
    id: UUID
    profiles: list[ProfileRecord]
    score: float
    independent_sources: int
    conflicts: list[str]


def _pair_score(a: ProfileRecord, b: ProfileRecord) -> float:
    signals = [
        similarity(a.display_name, b.display_name),
        similarity(a.username, b.username),
        similarity(a.organization, b.organization),
        similarity(a.location, b.location),
        similarity(a.bio, b.bio),
    ]
    # Missing fields contribute zero; strongest identity anchors dominate.
    present = [s for s in signals if s > 0]
    if not present:
        return 0.0
    return (sum(sorted(present, reverse=True)[:4]) / min(4, len(present))) * 100


def cluster_profiles(profiles: list[ProfileRecord], threshold: float = 72.0) -> list[IdentityCluster]:
    """Cluster records conservatively; no single field can create a cluster."""
    groups: list[list[ProfileRecord]] = []
    for profile in profiles:
        placed = False
        for group in groups:
            best = max(_pair_score(profile, existing) for existing in group)
            if best >= threshold:
                group.append(profile)
                placed = True
                break
        if not placed:
            groups.append([profile])

    clusters: list[IdentityCluster] = []
    for group in groups:
        pair_scores = [_pair_score(a, b) for a, b in combinations(group, 2)]
        score = sum(pair_scores) / len(pair_scores) if pair_scores else 0.0
        sources = len({p.platform.casefold() for p in group})
        clusters.append(IdentityCluster(uuid4(), group, round(score, 2), sources, detect_conflicts(group)))
    return sorted(clusters, key=lambda c: (c.independent_sources, c.score), reverse=True)


def resolve_identity(query: ProfileRecord, profiles: list[ProfileRecord]) -> list[ResolutionResult]:
    """Resolve a query against discovered records, rewarding independent corroboration."""
    clusters = cluster_profiles(profiles)
    results: list[ResolutionResult] = []
    for cluster in clusters:
        candidate = Candidate(name=cluster.profiles[0].display_name or "Unknown", profiles=cluster.profiles)
        from .resolver import rank_candidates
        base = rank_candidates(query, [candidate])[0]
        corroboration = min(15.0, max(0, cluster.independent_sources - 1) * 7.5)
        penalty = min(20.0, len(cluster.conflicts) * 10.0)
        score = max(0.0, min(100.0, base.score + corroboration - penalty))
        if cluster.conflicts and score >= 60:
            status = ResolutionStatus.CONFLICT
        elif score >= 90 and cluster.independent_sources >= 2:
            status = ResolutionStatus.VERIFIED
        elif score >= 75:
            status = ResolutionStatus.PROBABLE
        elif score >= 50:
            status = ResolutionStatus.POSSIBLE
        else:
            status = ResolutionStatus.INSUFFICIENT_EVIDENCE
        results.append(base.model_copy(update={
            "candidate_id": cluster.id,
            "score": round(score, 2),
            "status": status,
            "conflicts": cluster.conflicts,
        }))
    return sorted(results, key=lambda r: r.score, reverse=True)
