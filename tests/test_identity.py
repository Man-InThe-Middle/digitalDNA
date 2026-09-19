from app.core.resolution.identity import cluster_profiles, resolve_identity
from app.models.domain import ProfileRecord, ResolutionStatus, SourceType


def test_same_person_clusters_across_independent_sources():
    profiles = [
        ProfileRecord(platform="GitHub", display_name="Rahul Sharma", username="rahuldev23", organization="OpenCompute Labs", location="Hyderabad", bio="Developer", source_type=SourceType.CODE),
        ProfileRecord(platform="LinkedIn", display_name="Rahul Sharma", username="rahul-sharma", organization="OpenCompute Labs", location="Hyderabad", bio="Developer", source_type=SourceType.PROFESSIONAL),
    ]
    clusters = cluster_profiles(profiles)
    assert len(clusters) == 1
    assert clusters[0].independent_sources == 2


def test_same_name_different_people_do_not_cluster():
    profiles = [
        ProfileRecord(platform="GitHub", display_name="Rahul Sharma", username="rahuldev23", organization="OpenCompute Labs", location="Hyderabad"),
        ProfileRecord(platform="LinkedIn", display_name="Rahul Sharma", username="rahulfinance", organization="Acme Finance", location="Mumbai"),
    ]
    clusters = cluster_profiles(profiles)
    assert len(clusters) == 2


def test_conflicting_cluster_is_not_silently_verified():
    query = ProfileRecord(platform="query", display_name="Rahul Sharma", username="rahuldev23", organization="OpenCompute Labs", location="Hyderabad", bio="Developer")
    profiles = [
        ProfileRecord(platform="GitHub", display_name="Rahul Sharma", username="rahuldev23", organization="OpenCompute Labs", location="Hyderabad", bio="Developer"),
        ProfileRecord(platform="LinkedIn", display_name="Rahul Sharma", username="rahul-sharma", organization="Acme Finance", location="Hyderabad", bio="Developer"),
    ]
    result = resolve_identity(query, profiles)[0]
    assert result.status in {ResolutionStatus.CONFLICT, ResolutionStatus.PROBABLE}
    assert result.conflicts
