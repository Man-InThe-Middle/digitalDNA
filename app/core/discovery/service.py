from __future__ import annotations

import asyncio

from app.models.domain import ProfileRecord
from .base import DiscoveryProvider, DiscoveryQuery


class DiscoveryService:
    def __init__(self, providers: list[DiscoveryProvider]):
        self.providers = providers

    async def discover(self, query: DiscoveryQuery) -> list[ProfileRecord]:
        if not self.providers:
            return []
        results = await asyncio.gather(*(p.discover(query) for p in self.providers), return_exceptions=True)
        merged: list[ProfileRecord] = []
        seen: set[tuple[str, str, str]] = set()
        for result in results:
            if isinstance(result, Exception):
                continue
            for profile in result:
                key = (profile.platform.lower(), (profile.username or "").lower(), str(profile.url or "").lower())
                if key in seen:
                    continue
                seen.add(key)
                merged.append(profile)
        return merged
