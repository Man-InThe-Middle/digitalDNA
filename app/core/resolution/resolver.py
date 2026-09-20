from __future__ import annotations

from app.models.domain import Candidate, ProfileRecord, ResolutionResult, ResolutionStatus
from app.core.evidence.conflicts import detect_conflicts
from .scorer import resolve_candidate


def classify(score: float, conflicts: list[str]) -> ResolutionStatus:
    if conflicts and score >= 70:
        return ResolutionStatus.CONFLICT
    if score >= 85:
        return ResolutionStatus.VERIFIED
    if score >= 70:
        return ResolutionStatus.PROBABLE
    if score >= 50:
        return ResolutionStatus.POSSIBLE
    return ResolutionStatus.INSUFFICIENT_EVIDENCE


def rank_candidates(query: ProfileRecord, candidates: list[Candidate]) -> list[ResolutionResult]:
    results: list[ResolutionResult] = []
    for candidate in candidates:
        score, signals = resolve_candidate(query, candidate)
        conflicts = detect_conflicts(candidate.profiles)
        results.append(
            ResolutionResult(
                candidate_id=candidate.id,
                score=round(score, 2),
                status=classify(score, conflicts),
                signals={k: round(v, 4) for k, v in signals.items()},
                supporting_evidence=[e.id for e in candidate.evidence],
                conflicts=conflicts,
                explanation=[
                    "Resolution is based on configured evidence signals and source corroboration.",
                    *(["Conflicting source claims were detected."] if conflicts else []),
                ],
            )
        )
    return sorted(results, key=lambda r: r.score, reverse=True)
