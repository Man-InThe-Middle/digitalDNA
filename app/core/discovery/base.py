from typing import Protocol
from app.models.domain import ProfileRecord


class DiscoveryQuery:
    def __init__(self, name: str, username: str | None = None):
        self.name = name
        self.username = username


class DiscoveryProvider(Protocol):
    async def discover(self, query: DiscoveryQuery) -> list[ProfileRecord]: ...
