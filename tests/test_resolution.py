from app.core.resolution.resolver import rank_candidates
from app.models.domain import Candidate, ProfileRecord, SourceType


def test_matching_candidate_ranks_high():
    query = ProfileRecord(platform="query", display_name="Rahul Sharma", username="rahuldev23", organization="OpenCompute Labs", location="Hyderabad", bio="Developer building open-source developer tooling.")
    candidate = Candidate(name="Rahul Sharma", profiles=[ProfileRecord(platform="GitHub", display_name="Rahul Sharma", username="rahuldev23", organization="OpenCompute Labs", location="Hyderabad", bio="Developer building open-source developer tooling.", source_type=SourceType.CODE)])
    result = rank_candidates(query, [candidate])[0]
    assert result.score >= 85


def test_conflict_is_surfaceable():
    query = ProfileRecord(platform="query", display_name="Rahul Sharma")
    candidate = Candidate(name="Rahul Sharma", profiles=[
        ProfileRecord(platform="A", display_name="Rahul Sharma", organization="Org A", location="Hyderabad"),
        ProfileRecord(platform="B", display_name="Rahul Sharma", organization="Org B", location="Hyderabad"),
    ])
    result = rank_candidates(query, [candidate])[0]
    assert result.conflicts
