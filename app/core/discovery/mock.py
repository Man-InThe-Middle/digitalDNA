from app.models.domain import ProfileRecord, SourceType
from .base import DiscoveryQuery


class MockDiscoveryProvider:
    """Deterministic demo provider; no external scraping or network access."""

    async def discover(self, query: DiscoveryQuery) -> list[ProfileRecord]:
        return [
            ProfileRecord(
                platform="GitHub",
                username="rahuldev23",
                display_name=query.name,
                organization="OpenCompute Labs",
                location="Hyderabad",
                source_type=SourceType.CODE,
                bio="Developer building open-source developer tooling.",
            ),
            ProfileRecord(
                platform="LinkedIn",
                username=None,
                display_name=query.name,
                organization="OpenCompute Labs",
                location="Hyderabad",
                source_type=SourceType.PROFESSIONAL,
                bio="Software engineer and hackathon mentor.",
            ),
        ]
