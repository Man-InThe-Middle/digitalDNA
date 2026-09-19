import pytest

from app.core.discovery.service import DiscoveryService
from app.core.discovery.base import DiscoveryQuery
from app.models.domain import ProfileRecord


class ProviderA:
    async def discover(self, query):
        return [ProfileRecord(platform="GitHub", username="rahuldev23", display_name=query.name)]


class ProviderB:
    async def discover(self, query):
        return [
            ProfileRecord(platform="GitHub", username="rahuldev23", display_name=query.name),
            ProfileRecord(platform="LinkedIn", username="rahul-sharma", display_name=query.name),
        ]


@pytest.mark.asyncio
async def test_discovery_service_deduplicates_profiles():
    profiles = await DiscoveryService([ProviderA(), ProviderB()]).discover(DiscoveryQuery("Rahul Sharma"))
    assert len(profiles) == 2
    assert {p.platform for p in profiles} == {"GitHub", "LinkedIn"}
