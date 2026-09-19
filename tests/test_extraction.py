from app.models.domain import ProfileRecord, SourceType
from app.core.extraction import extract_from_profiles
from app.core.evidence.conflicts import detect_claim_conflicts


def test_extraction_creates_evidence_from_profile():
    profile = ProfileRecord(
        platform="GitHub",
        username="rahuldev23",
        display_name="Rahul Sharma",
        organization="OpenCompute Labs",
        location="Hyderabad",
        bio="Developer building tools.",
        source_type=SourceType.CODE,
    )
    candidates, evidence = extract_from_profiles([profile])
    assert len(candidates) == 1
    assert {e.signal_type for e in evidence} >= {"name", "username", "organization", "location", "bio"}


def test_conflicts_are_surfaced():
    profiles = [
        ProfileRecord(platform="a", display_name="Rahul Sharma", organization="OpenCompute Labs", location="Hyderabad"),
        ProfileRecord(platform="b", display_name="Rahul Sharma", organization="Different Labs", location="Bengaluru"),
    ]
    _, evidence = extract_from_profiles(profiles)
    conflicts = detect_claim_conflicts(evidence)
    assert any("organization" in c for c in conflicts)
    assert any("location" in c for c in conflicts)
