from __future__ import annotations

import asyncio

from app.models.domain import ProfileRecord
from .base import DiscoveryProvider, DiscoveryQuery


class DiscoveryService:

    def __init__(
        self,
        providers: list[DiscoveryProvider],
        retries: int = 2,
    ):
        self.providers = providers
        self.retries = retries

    async def _run_provider(
        self,
        provider,
        query: DiscoveryQuery,
    ) -> list[ProfileRecord]:

        name = getattr(
            provider,
            "name",
            provider.__class__.__name__,
        )

        for attempt in range(1, self.retries + 2):

            try:

                print(
                    f"[DigitalDNA] "
                    f"{name}: attempt {attempt}"
                )

                results = await asyncio.wait_for(
                    provider.discover(query),
                    timeout=20,
                )

                print(
                    f"[DigitalDNA] "
                    f"{name}: {len(results)} profile(s)"
                )

                return results

            except asyncio.TimeoutError:

                print(
                    f"[DigitalDNA] "
                    f"{name}: TIMEOUT "
                    f"(attempt {attempt})"
                )

            except Exception as exc:

                print(
                    f"[DigitalDNA] "
                    f"{name}: FAILED "
                    f"(attempt {attempt}) "
                    f"{type(exc).__name__}: {exc}"
                )

            if attempt <= self.retries:

                await asyncio.sleep(
                    1.5 * attempt
                )

        print(
            f"[DigitalDNA] "
            f"{name}: permanently failed"
        )

        return []

    async def discover(
        self,
        query: DiscoveryQuery,
    ) -> list[ProfileRecord]:

        if not self.providers:

            print(
                "[DigitalDNA] "
                "No discovery providers configured"
            )

            return []

        print(
            f"[DigitalDNA] Discovery started for "
            f"{query.name!r}"
        )

        provider_results = await asyncio.gather(
            *(
                self._run_provider(
                    provider,
                    query,
                )
                for provider in self.providers
            )
        )

        merged: list[ProfileRecord] = []
        seen: set[tuple[str, str, str]] = set()

        for results in provider_results:

            for profile in results:

                key = (
                    profile.platform.lower(),
                    (
                        profile.username or ""
                    ).lower(),
                    (
                        str(profile.url or "")
                    ).lower(),
                )

                if key in seen:
                    continue

                seen.add(key)
                merged.append(profile)

        print(
            f"[DigitalDNA] Discovery complete: "
            f"{len(merged)} unique profile(s)"
        )

        return merged